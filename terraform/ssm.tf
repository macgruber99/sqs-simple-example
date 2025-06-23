resource "aws_ssm_parameter" "queue_url" {
  name        = local.ssm_param_path_queue_url
  description = "The URL of the SQS queue"
  type        = "String"
  value       = module.sqs.queue_url

  tags = local.tags
}

resource "aws_ssm_parameter" "bucket_name" {
  name        = local.ssm_param_path_bucket_name
  description = "The name of the S3 bucket"
  type        = "String"
  value       = module.s3_bucket.s3_bucket_id

  tags = local.tags
}
