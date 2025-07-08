from dota_auto_eval import (
    DOTAEvaluator,
    AuthenticationError,
    TaskSubmissionError,
    DOTAEvalError
)

# 创建评估器实例
evaluator = DOTAEvaluator(
    base_url="http://8.152.99.246:5000/",
    api_key="b684d3204745b4d82bcc94bc742b46dc18567b664c15756fd2d270ffd3491e33"
)

try:
    # 创建训练任务
    task_result = evaluator.create_training_task(
        name="YOLOv8 Training",
        description="Training YOLOv8 on DOTA dataset",
        server_id=1
    )
    print(f"创建的训练任务ID: {task_result['task_id']}")
    
    # 提交训练结果
    result = evaluator.submit_training_result(
        task_id=task_result['task_id'],
        epoch=10,
        eval_file="/home/dota_auto_eval_new/dota_auto_eval/temp/20250708_001352_4142.zip"
    )
    
    print(f"\n=== 提交结果 ===")
    print(result)

except AuthenticationError as e:
    print(f"认证失败: {e}")
except TaskSubmissionError as e:
    print(f"任务提交失败: {e}")
except DOTAEvalError as e:
    print(f"评估错误: {e}")
except Exception as e:
    print(f"未预期的错误: {str(e)}")
    raise