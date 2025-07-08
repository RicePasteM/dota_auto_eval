import os
from typing import Optional, Dict, Any
import requests
from .exceptions import (
    AuthenticationError,
    TaskSubmissionError
)

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
    
    def create_training_task(self, name: str, description: Optional[str] = None, server_id: int = 1) -> Dict[str, Any]:
        """
        Create a new training task
        
        Args:
            name: Training task name
            description: Training task description (optional)
            server_id: Server ID (default: 1)
            
        Returns:
            dict: Dictionary containing task information including task_id
            
        Raises:
            TaskSubmissionError: Task creation failed
            AuthenticationError: API key authentication failed
        """
        try:
            # 按照后端要求构建数据
            data = {
                'task_name': name,
                'server_id': server_id
            }
            if description:
                data['description'] = description
                
            response = self.session.post(
                f"{self.base_url}/api/training",
                json=data
            )
            
            if response.status_code == 401:
                raise AuthenticationError("API key authentication failed")
            elif response.status_code != 201 and response.status_code != 200:  # 后端返回201状态码
                raise TaskSubmissionError(f"Training task creation failed: {response.text}")
                
            result = response.json()
            
            # Print the task URL to console
            task_url = f"{self.base_url}/training/{result['task_id']}"
            print(f"Training task created successfully! Task URL: {task_url}")
            
            return result
            
        except requests.RequestException as e:
            raise TaskSubmissionError(f"Network error during task creation: {str(e)}")
    
    def submit_training_result(self, task_id: str, epoch: int, eval_file: str) -> Dict[str, Any]:
        """
        Submit training result for a specific epoch
        
        Args:
            task_id: Training task ID
            epoch: Training epoch
            eval_file: Evaluation file path
            
        Returns:
            dict: Dictionary containing submission result
            
        Raises:
            TaskSubmissionError: Result submission failed
            AuthenticationError: API key authentication failed
        """
        if not os.path.exists(eval_file):
            raise TaskSubmissionError(f"Evaluation file does not exist: {eval_file}")
            
        try:
            with open(eval_file, 'rb') as f:
                files = {'eval_file': f}
                data = {
                    'epoch': epoch
                }
                
                response = self.session.post(
                    f"{self.base_url}/api/training/{task_id}/epoch",
                    data=data,
                    files=files
                )
                
            if response.status_code == 401:
                raise AuthenticationError("API key authentication failed")
            elif response.status_code != 200:
                raise TaskSubmissionError(f"Training result submission failed: {response.text}")
                
            result = response.json()
            
            # Print the result URL to console
            result_url = f"{self.base_url}/training/{task_id}"
            print(f"Training result submitted successfully! Result URL: {result_url}")
            
            return result
            
        except requests.RequestException as e:
            raise TaskSubmissionError(f"Network error during result submission: {str(e)}") 