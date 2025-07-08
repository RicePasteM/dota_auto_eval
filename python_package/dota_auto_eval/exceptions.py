class DOTAEvalError(Exception):
    """DOTA Evaluation Base Exception Class"""
    pass

class AuthenticationError(DOTAEvalError):
    """Authentication Failed Exception"""
    pass

class TaskSubmissionError(DOTAEvalError):
    """Task Submission Failed Exception"""
    pass 