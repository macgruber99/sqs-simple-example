config = {
    "max_obj_size": 262144,  # 256 KB, max size for SQS message
    "ssm_param_path": "/sqs-simple-example",
    "required_ssm_params": ["input-bucket-name", "queue-url"],
}
