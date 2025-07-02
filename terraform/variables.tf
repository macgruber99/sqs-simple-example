variable "project_name" {
  description = "The name of the project for which AWS resources are being created"
  type        = string
  default     = "sqs-simple-example"
}

variable "aws_region" {
  description = "The AWS region where the SQS queue will be created"
  type        = string
  default     = "us-west-2"
}

variable "additional_tags" {
  description = "A map of tags to assign to AWS resources"
  type        = map(string)

  default = {
    Owner = "Erik Green"
  }
}

variable "lambda_memory" {
  description = "The amount of memory dedicated to the Lambda function"
  type        = number
  default     = 256
}

variable "sqs_max_lambda_invocations" {
  description = "Limits number of concurrent Lambda executions that SQS event source can invoke."
  type        = number
  default     = 20
}

variable "lambda_logs_retention_days" {
  description = "The number of days Lambda function CloudWatch logs are retained"
  type        = number
  default     = 1 # Not keeping logs since this is just an example
}

variable "visibility_timeout" {
  description = "The visibility timeout for the SQS queue in seconds"
  type        = number
  default     = 900 # i.e. 15 minutes
}

variable "alerts_email" {
  description = "Email address to receive alerts for the SQS queue"
  type        = string
  default     = "erikgreen@gmail.com"
}

variable "codebuild_compute_type" {
  description = "The CodeBuild compute type"
  type        = string
  default     = "BUILD_GENERAL1_SMALL"
}
variable "codebuild_image" {
  description = "The image to use for the CodeBuild project"
  type        = string
  default     = "aws/codebuild/amazonlinux-x86_64-standard:5.0"
}

variable "codebuild_env_type" {
  description = "Type of CodeBuild build environment to use"
  type        = string
  default     = "LINUX_CONTAINER"
}

variable "codebuild_timeout" {
  description = "The number of minutes CodeBuild executes before timing out"
  type        = number
  default     = 10
}

variable "github_repo" {
  description = "value"
  type        = string
  default     = "https://github.com/macgruber99/sqs-simple-example.git"
}

variable "github_source_version" {
  description = "The GitHub repo branch to use"
  type        = string
  default     = "main"
}

variable "buildspec_file" {
  description = "The relative path to the Buildspec file."
  type        = string
  default     = "cicd/buildspec.yml"
}
