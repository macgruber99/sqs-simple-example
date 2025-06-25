module "lambda_sqs_producer" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "7.21.0"

  function_name = "${var.project_name}-producer"
  description   = "A simple Lambda function SQS producer"
  handler       = "producer/lambda_function.lambda_handler"
  runtime       = "python3.13"
  memory_size   = 256

  create_package         = false
  local_existing_package = "../lambdas/producer/package.zip"

  policy_statements = {
    sms_parameter_store_access = {
      actions = [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParameterHistory",
        "ssm:DescribeParameters"
      ]

      resources = [
        "arn:aws:ssm:*:*:parameter${local.ssm_param_path_queue_url}"
      ]
    }

    sqs_access = {
      actions = [
        "sqs:SendMessage"
      ]

      resources = [
        module.sqs.queue_arn
      ]
    }
  }

  attach_policy_statements = true

  environment_variables = {
    # The queue URL could also be put directly in the environment variable,
    # but I'm using an SSM parameter to demonstrate how to use SSM parameters.
    SSM_PARAM_PATH = local.ssm_param_path_queue_url
  }

  # Not keeping logs since this is just an example
  cloudwatch_logs_retention_in_days = 1

  tags = local.tags
}

module "lambda_sqs_consumer" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "7.21.0"

  function_name = "${var.project_name}-consumer"
  description   = "A simple Lambda function SQS consumer"
  handler       = "consumer/lambda_function.lambda_handler"
  runtime       = "python3.13"
  memory_size   = 256

  create_package         = false
  local_existing_package = "../lambdas/consumer/package.zip"

  policy_statements = {
    sms_parameter_store_access = {
      actions = [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParameterHistory",
        "ssm:DescribeParameters"
      ]

      resources = [
        "arn:aws:ssm:*:*:parameter${local.ssm_param_path_bucket_name}"
      ]
    }

    sqs_access = {
      actions = [
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes",
        "sqs:ReceiveMessage"
      ]

      resources = [
        module.sqs.queue_arn
      ]
    }

    s3_access = {
      actions = [
        "s3:PutObject",
        "s3:PutObjectAcl", // Optional, if you need to manage ACLs
        "s3:ListBucket"
      ]

      resources = [
        module.s3_bucket.s3_bucket_arn,
        "${module.s3_bucket.s3_bucket_arn}/*"
      ]
    }
  }

  attach_policy_statements = true

  event_source_mapping = {
    sqs = {
      event_source_arn        = module.sqs.queue_arn
      function_response_types = ["ReportBatchItemFailures"]

      scaling_config = {
        maximum_concurrency = 20
      }

      metrics_config = {
        metrics = ["EventCount"]
      }
    }
  }

  environment_variables = {
    # The S3 bucket name could be put directly in the environment variable, but
    # I'm using an SSM parameter to demonstrate how to use SSM parameters.
    SSM_PARAM_PATH = local.ssm_param_path_bucket_name
  }

  # Not keeping logs since this is just an example
  cloudwatch_logs_retention_in_days = 1

  tags = local.tags
}
