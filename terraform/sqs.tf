module "sqs" {
  source  = "terraform-aws-modules/sqs/aws"
  version = "4.3.1"

  name                       = var.project_name
  kms_master_key_id          = "alias/aws/sqs"
  visibility_timeout_seconds = var.visibility_timeout

  create_dlq = true

  redrive_policy = {
    # since this is an example project, send to DLQ after 1 failure
    maxReceiveCount = 1
  }

  tags = local.tags
}
