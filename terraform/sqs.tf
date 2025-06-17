module "sqs" {
  source  = "terraform-aws-modules/sqs/aws"
  version = "4.3.1"

  name                       = var.project_name
  kms_master_key_id          = var.kms_master_key_id
  visibility_timeout_seconds = var.visibility_timeout

  tags = var.tags
}
