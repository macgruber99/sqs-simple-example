module "lambda_sqs_producer" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "7.21.0"

  function_name = "${var.project_name}-producer"
  description   = "A simple Lambda function SQS producer"
  handler       = "producer/lambda_function.lambda_handler"
  runtime       = "python3.13"
  memory_size   = var.lambda_memory

  create_package         = false
  local_existing_package = "../lambdas/producer/package.zip"

  policy_statements = {
    ssm_parameter_store_access = {
      actions = [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath"
      ]

      resources = [
        format(
          "arn:aws:ssm:%s:%s:parameter/%s*",
          var.aws_region,
          data.aws_caller_identity.current.account_id,
          var.project_name
        )
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

  cloudwatch_logs_retention_in_days = var.lambda_logs_retention_days

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
  memory_size   = var.lambda_memory

  create_package         = false
  local_existing_package = "../lambdas/consumer/package.zip"

  policy_statements = {
    ssm_parameter_store_access = {
      actions = [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath"
      ]

      resources = [
        format(
          "arn:aws:ssm:%s:%s:parameter/%s*",
          var.aws_region,
          data.aws_caller_identity.current.account_id,
          var.project_name
        )
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
        maximum_concurrency = var.sqs_max_lambda_invocations
      }

      metrics_config = {
        metrics = ["EventCount"]
      }
    }
  }

  cloudwatch_logs_retention_in_days = var.lambda_logs_retention_days

  tags = local.tags
}
