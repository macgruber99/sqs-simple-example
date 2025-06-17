module "lambda_sqs_producer" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "7.21.0"

  function_name = "${var.project_name}-producer"
  description   = "A simple Lambda function SQS producer"
  handler       = "producer/lambda_function.lambda_handler"
  runtime       = "python3.13"

  source_path            = "../lambdas/producer/src/producer/"
  local_existing_package = "../lambdas/producer/package.zip"

  tags = var.tags
}
