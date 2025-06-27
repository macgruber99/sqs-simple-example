# create "input" and an "output" buckets
module "s3_bucket" {
  for_each = local.buckets

  source  = "terraform-aws-modules/s3-bucket/aws"
  version = "4.11.0"

  bucket = "${var.project_name}-${each.key}"

  server_side_encryption_configuration = {
    rule = {
      bucket_key_enabled = true

      apply_server_side_encryption_by_default = {
        sse_algorithm = "AES256"
      }
    }
  }

  lifecycle_rule = [
    {
      id      = "expire-objects"
      enabled = true

      # since this project is just an example, delete objects after 1 day
      expiration = {
        days = 1
      }

      noncurrent_version_expiration = {
        days = 1
      }

      abort_incomplete_multipart_upload = {
        days_after_initiation = 1
      }
    }
  ]

  tags = local.tags
}

resource "aws_s3_bucket_notification" "trigger" {
  bucket = module.s3_bucket["input"].s3_bucket_id

  lambda_function {
    lambda_function_arn = module.lambda_sqs_producer.lambda_function_arn
    events              = ["s3:ObjectCreated:*"]
  }

  depends_on = [
    aws_lambda_permission.allow_bucket
  ]
}
