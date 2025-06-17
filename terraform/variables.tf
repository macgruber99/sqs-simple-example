variable "project_name" {
  description = "The name of the project for which AWS resources are being created."
  type        = string
  default     = "sqs-simple-example"
}

variable "aws_region" {
  description = "The AWS region where the SQS queue will be created."
  type        = string
  default     = "us-west-2"
}

variable "tags" {
  description = "A map of tags to assign to AWS resources."
  type        = map(string)
  default     = {}
}

variable "visibility_timeout" {
  description = "The visibility timeout for the SQS queue in seconds."
  type        = number
  default     = 900 # i.e. 15 minutes
}

variable "kms_master_key_id" {
  description = "The KMS master key ID for server-side encryption of the SQS queue."
  type        = string
  default     = "alias/aws/sqs" # Default AWS managed key
}
