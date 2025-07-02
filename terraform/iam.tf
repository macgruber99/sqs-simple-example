data "aws_iam_policy_document" "codebuild_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["codebuild.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "sqs_simple_example_codebuild" {
  name               = "${var.project_name}-codebuild-role"
  path               = "/codebuild/"
  assume_role_policy = data.aws_iam_policy_document.codebuild_assume_role.json
}

data "aws_iam_policy_document" "codebuild_sqs_simple_example" {
  #checkov:skip=CKV_AWS_111:Ensure IAM policies does not allow write access without constraints
  #checkov:skip=CKV_AWS_356:Ensure no IAM policies documents allow "*" as a statement's resource for restrictable actions
  statement {
    effect = "Allow"

    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]

    resources = ["*"]
  }

  statement {
    effect = "Allow"
    actions = [
      "s3:PutObject",
      "s3:GetBucketAcl",
      "s3:GetBucketLocation"
    ]

    resources = [
      module.s3_bucket["input"].s3_bucket_arn,
      module.s3_bucket["output"].s3_bucket_arn,
      "${module.s3_bucket["input"].s3_bucket_arn}/*",
      "${module.s3_bucket["output"].s3_bucket_arn}/*"
    ]
  }

  statement {
    effect  = "Allow"
    actions = ["ssm:*Parameter*"]

    resources = [
      aws_ssm_parameter.queue_url.arn
    ]
  }

  statement {
    effect = "Allow"

    actions = [
      "codeconnections:GetConnection",
      "codeconnections:GetConnectionToken",
      "codeconnections:ListConnections",
      "codeconnections:TagResource",
      "codeconnections:UntagResource",
      "codeconnections:UseConnection"
    ]

    resources = [
      data.aws_ssm_parameter.codeconnections_connection.value
    ]
  }
}

resource "aws_iam_policy" "codebuild_sqs_simple_example" {
  name        = "${var.project_name}-codebuild-policy"
  description = "Policy for CodeBuild role for ${var.project_name} project"
  policy      = data.aws_iam_policy_document.codebuild_sqs_simple_example.json
}

resource "aws_iam_role_policy_attachment" "codebuild_sqs_simple_example" {
  role       = aws_iam_role.sqs_simple_example_codebuild.name
  policy_arn = aws_iam_policy.codebuild_sqs_simple_example.arn
}
