data "aws_ssm_parameter" "codeconnections_connection" {
  name = "/core-infra/codeconnections-connection"
}

data "aws_ssm_parameter" "codebuild_logs_bucket_id" {
  name = "/core-infra/codebuild-logs-bucket-id"
}
