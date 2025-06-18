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
  }

  attach_policy_statements = true

  tags = var.tags
}
