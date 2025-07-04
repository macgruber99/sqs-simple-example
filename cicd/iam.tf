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

resource "aws_iam_policy" "codebuild_sqs_simple_example" {
  name        = "${var.project_name}-codebuild-policy"
  description = "Policy for CodeBuild role for ${var.project_name} project"

  policy = templatefile(
    "${path.module}/codebuild-policy.tftpl",
    {
      Account     = data.aws_caller_identity.current.account_id,
      Region      = var.aws_region,
      ProjectName = var.project_name
    }
  )
}

resource "aws_iam_role_policy_attachment" "codebuild_sqs_simple_example" {
  role       = aws_iam_role.sqs_simple_example_codebuild.name
  policy_arn = aws_iam_policy.codebuild_sqs_simple_example.arn
}
