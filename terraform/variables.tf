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

variable "additional_tags" {
  description = "A map of tags to assign to AWS resources."
  type        = map(string)

  default = {
    Owner = "Erik Green"
  }
}

variable "visibility_timeout" {
  description = "The visibility timeout for the SQS queue in seconds."
  type        = number
  default     = 900 # i.e. 15 minutes
}

variable "alerts_email" {
  description = "Email address to receive alerts for the SQS queue."
  type        = string
  default     = "erikgreen@gmail.com"
}
