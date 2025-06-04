from dota_auto_eval import (
    DOTAEvaluator,
    AuthenticationError,
    TaskSubmissionError,
    TimeoutError,
    DOTAEvalError,
    V1Task1Parser
)
from typing import Dict, Any

# Create evaluator instance
evaluator = DOTAEvaluator(
    base_url="http://127.0.0.1:5000",
    api_key="b684d3204745b4d82bcc94bc742b46dc18567b664c15756fd2d270ffd3491e33"
)

try:
    # Check remaining evaluation counts
    remaining = evaluator.get_remaining_counts(server_id=1)
    print(f"Remaining evaluation counts: {remaining}")

    # Submit evaluation task
    task_id = evaluator.submit_eval(
        server_id=1,
        eval_file="C:\\Users\\ricepastem\\Desktop\\Task1.zip"
    )
    print(f"Task ID: {task_id}")

    # Wait for result (maximum 3 minutes)
    result = evaluator.wait_for_result(
        task_id,
        timeout=180,
        parser=V1Task1Parser(),
        verbose=True  # Enable verbose logging
    )
    
    # Print parsed result
    if 'error' in result:
        print(f"\n=== Evaluation Failed ===")
        print(f"Error message: {result['error']}")
        if 'raw_message' in result:
            print(f"\nRaw message:")
            print(result['raw_message'])
    else:
        print("\n=== Evaluation Results ===")
        print(result)

except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except TaskSubmissionError as e:
    print(f"Task submission failed: {e}")
except TimeoutError as e:
    print(f"Wait timeout: {e}")
except DOTAEvalError as e:
    print(f"Evaluation error: {e}")
except Exception as e:
    print(f"Unexpected error: {str(e)}")
    raise