resource "aws_ssm_parameter" "queue_url" {
  #checkov:skip=CKV2_AWS_34:parameter not sensitive, no need to encrypt
  name        = "/${var.project_name}/queue-url"
  description = "The URL of the SQS queue"
  type        = "String"
  value       = module.sqs.queue_url

  tags = local.tags
}

resource "aws_ssm_parameter" "queue_arn" {
  #checkov:skip=CKV2_AWS_34:parameter not sensitive, no need to encrypt
  name        = "/${var.project_name}/queue-arn"
  description = "The ARN of the SQS queue"
  type        = "String"
  value       = module.sqs.queue_arn

  tags = local.tags
}

resource "aws_ssm_parameter" "bucket_name" {
  #checkov:skip=CKV2_AWS_34:parameter not sensitive, no need to encrypt
  for_each = local.buckets

  name        = "/${var.project_name}/${each.key}-bucket-name"
  description = "The name of the S3 bucket"
  type        = "String"
  #value       = module.s3_bucket.s3_bucket_id
  value = module.s3_bucket[each.key].s3_bucket_id

  tags = local.tags
}
