class DOTAEvalError(Exception):
    """DOTA Evaluation Base Exception Class"""
    pass

class AuthenticationError(DOTAEvalError):
    """Authentication Failed Exception"""
    pass

class TaskSubmissionError(DOTAEvalError):
    """Task Submission Failed Exception"""
    pass

class TaskStatusError(DOTAEvalError):
    """Task Status Retrieval Failed Exception"""
    pass

class TimeoutError(DOTAEvalError):
    """Task Timeout Exception"""
    pass 