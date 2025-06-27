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
      ]

      resources = [
        aws_ssm_parameter.queue_url.arn,
        aws_ssm_parameter.bucket_name["input"].arn
      ]
    }

    s3_access = {
      actions = [
        "s3:GetObject",
        "s3:ListBucket"
      ]

      resources = [
        module.s3_bucket["input"].s3_bucket_arn,
        "${module.s3_bucket["input"].s3_bucket_arn}/*"
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
    # The AWS resource identifiers themselves could be put in env vars, but
    # here SSM parameters are used and parameter paths are put in env vars.
    SSM_PARAM_QUEUE  = aws_ssm_parameter.queue_url.name
    SSM_PARAM_BUCKET = aws_ssm_parameter.bucket_name["input"].name
  }

  # Not keeping logs since this is just an example
  cloudwatch_logs_retention_in_days = 1

  tags = local.tags
}

resource "aws_lambda_permission" "allow_bucket" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda_sqs_producer.lambda_function_name
  principal     = "s3.amazonaws.com"
  source_arn    = module.s3_bucket["input"].s3_bucket_arn
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
      ]

      resources = [
        aws_ssm_parameter.bucket_name["output"].arn
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
        "s3:ListBucket"
      ]

      resources = [
        module.s3_bucket["output"].s3_bucket_arn,
        "${module.s3_bucket["output"].s3_bucket_arn}/*"
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
    # The AWS resource identifier itself could be put in the env var, but here
    # an SSM parameter is used and the parameter path is put in the env var.
    SSM_PARAM_BUCKET = aws_ssm_parameter.bucket_name["output"].name
  }

  # Not keeping logs since this is just an example
  cloudwatch_logs_retention_in_days = 1

  tags = local.tags
}
