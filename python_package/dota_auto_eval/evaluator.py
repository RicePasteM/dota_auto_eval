import os
import time
from typing import Optional, Dict, Any, List
import requests
from datetime import datetime
from .exceptions import (
    AuthenticationError,
    TaskSubmissionError,
    TaskStatusError,
    TimeoutError
)
from .parsers import ResultParser

class DOTAEvaluator:
    """DOTA Evaluator Class"""
    
    def __init__(self, base_url: str, api_key: str):
        """
        Initialize evaluator
        
        Args:
            base_url: API server base URL
            api_key: API key
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': api_key
        })
        self.default_parser = ResultParser()
    
    def submit_eval(self, server_id: int, eval_file: str) -> str:
        """
        Submit evaluation task
        
        Args:
            server_id: Server ID
            eval_file: Evaluation file path
            
        Returns:
            task_id: Task ID
            
        Raises:
            TaskSubmissionError: Task submission failed
            AuthenticationError: API key authentication failed
        """
        if not os.path.exists(eval_file):
            raise TaskSubmissionError(f"Evaluation file does not exist: {eval_file}")
            
        try:
            with open(eval_file, 'rb') as f:
                files = {'eval_file': f}
                data = {'server_id': server_id}
                response = self.session.post(
                    f"{self.base_url}/api/eval/submit",
                    data=data,
                    files=files
                )
                
            if response.status_code == 401:
                raise AuthenticationError("API key authentication failed")
            elif response.status_code != 200:
                raise TaskSubmissionError(f"Task submission failed: {response.text}")
                
            result = response.json()
            return result['task_id']
            
        except requests.RequestException as e:
            raise TaskSubmissionError(f"Network error during task submission: {str(e)}")
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get task status
        
        Args:
            task_id: Task ID
            
        Returns:
            dict: Dictionary containing task status information
            
        Raises:
            TaskStatusError: Failed to get task status
            AuthenticationError: API key authentication failed
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/eval/task/{task_id}"
            )
            
            if response.status_code == 401:
                raise AuthenticationError("API key authentication failed")
            elif response.status_code != 200:
                raise TaskStatusError(f"Failed to get task status: {response.text}")
                
            return response.json()
            
        except requests.RequestException as e:
            raise TaskStatusError(f"Network error while getting task status: {str(e)}")
    
    def wait_for_result(
        self,
        task_id: str,
        timeout: int = 180,
        poll_interval: int = 10,
        parser: Optional[ResultParser] = None,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Wait and get evaluation results
        
        Args:
            task_id: Task ID
            timeout: Timeout in seconds, default 180 seconds
            poll_interval: Polling interval in seconds, default 10 seconds
            parser: Result parser, if None uses default parser
            verbose: Whether to output verbose logs, default False
            
        Returns:
            Dict[str, Any]: Parsed result dictionary
            
        Raises:
            TimeoutError: Wait timeout
            TaskStatusError: Failed to get task status
        """
        if parser is None:
            parser = self.default_parser
            
        start_time = time.time()
        processed_messages = set()  # Used to track processed messages
        
        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Task result wait timeout: {timeout} seconds")
                
            try:
                status = self.get_task_status(task_id)
                messages = status.get('messages', [])
                
                # Check for new messages
                new_messages = []
                for msg in messages:
                    msg_content = msg.get('message', '')
                    if msg_content not in processed_messages:
                        new_messages.append(msg)
                        processed_messages.add(msg_content)
                
                # Check for completion messages
                for msg in messages:
                    message = msg.get('message', '')
                    if msg.get('type') == 'success':
                        try:
                            result = parser.parse(message)
                            return result
                        except Exception as e:
                            if verbose:
                                print(f"Result parsing failed: {str(e)}")
                                print("Complete raw message:")
                                print(message)
                            return {'raw_message': message, 'error': str(e)}
                    elif msg.get('type') in ['error', 'warning']:
                        if verbose:
                            print(f"Found error message: {message}")
                        return {'error': message}
                
                # Output new messages
                if verbose and new_messages:
                    for msg in new_messages:
                        print(msg.get('message', ''))
                
                time.sleep(poll_interval)
                
            except TaskStatusError as e:
                if verbose:
                    print(f"Failed to get task status: {str(e)}")
                raise TaskStatusError(f"Failed to poll task status: {str(e)}")
    
    def get_remaining_counts(self, server_id: int) -> int:
        """
        Get remaining evaluation counts for server
        
        Args:
            server_id: Server ID
            
        Returns:
            int: Remaining evaluation counts
            
        Raises:
            TaskStatusError: Failed to get remaining counts
            AuthenticationError: API key authentication failed
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/eval/remaining_counts/{server_id}"
            )
            
            if response.status_code == 401:
                raise AuthenticationError("API key authentication failed")
            elif response.status_code != 200:
                raise TaskStatusError(f"Failed to get remaining counts: {response.text}")
                
            result = response.json()
            return result['remaining_counts']
            
        except requests.RequestException as e:
            raise TaskStatusError(f"Network error while getting remaining counts: {str(e)}")
    
    def get_eval_logs(
        self,
        page: int = 1,
        per_page: int = 20,
        server_id: Optional[int] = None,
        username: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get evaluation logs
        
        Args:
            page: Page number, default 1
            per_page: Items per page, default 20
            server_id: Server ID filter
            username: Username filter
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)
            
        Returns:
            dict: Dictionary containing log list and total count
            
        Raises:
            TaskStatusError: Failed to get logs
            AuthenticationError: API key authentication failed
        """
        try:
            params = {
                'page': page,
                'per_page': per_page
            }
            
            if server_id is not None:
                params['server_id'] = server_id
            if username is not None:
                params['username'] = username
            if start_date is not None:
                params['start_date'] = start_date
            if end_date is not None:
                params['end_date'] = end_date
                
            response = self.session.get(
                f"{self.base_url}/api/eval/logs",
                params=params
            )
            
            if response.status_code == 401:
                raise AuthenticationError("API key authentication failed")
            elif response.status_code != 200:
                raise TaskStatusError(f"Failed to get evaluation logs: {response.text}")
                
            return response.json()
            
        except requests.RequestException as e:
            raise TaskStatusError(f"Network error while getting evaluation logs: {str(e)}") 