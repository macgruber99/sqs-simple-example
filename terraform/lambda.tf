module "lambda_sqs_producer" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "7.21.0"

  function_name = "${var.project_name}-producer"
  description   = "A simple Lambda function SQS producer"
  handler       = "producer/lambda_function.lambda_handler"
  runtime       = "python3.13"

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
        "arn:aws:ssm:*:*:parameter/${var.project_name}/*"
      ]
    }
    
    sqs_access = {
      actions  = [
        "sqs:SendMessage"
      ]

      resources = [
        module.sqs.queue_arn
      ]
    }
  }

  attach_policy_statements = true

  tags = var.tags
}

module "lambda_sqs_consumer" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "7.21.0"

  function_name = "${var.project_name}-consumer"
  description   = "A simple Lambda function SQS consumer"
  handler       = "consumer/lambda_function.lambda_handler"
  runtime       = "python3.13"

  create_package         = false
  local_existing_package = "../lambdas/consumer/package.zip"

  policy_statements = {    
    sqs_access = {
      actions  = [
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes",
        "sqs:ReceiveMessage"
      ]
        
      resources = [
        module.sqs.queue_arn
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

  tags = var.tags
}
