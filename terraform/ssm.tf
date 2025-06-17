resource "aws_ssm_parameter" "queue_url" {
  name        = "/${var.project_name}/queue-url"
  description = "The URL of the SQS queue"
  type        = "String"
  value       = module.sqs.queue_url

  tags = var.tags
}