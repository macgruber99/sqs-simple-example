resource "aws_codebuild_project" "sqs_simple_example" {
  name          = var.project_name
  description   = "Codebuild project for ${var.project_name}"
  build_timeout = 10
  service_role  = aws_iam_role.sqs_simple_example_codebuild.arn

  artifacts {
    type = "NO_ARTIFACTS"
  }

  #   cache {
  #     type     = "S3"
  #     location = aws_s3_bucket.example.bucket
  #   }

  environment {
    compute_type                = "BUILD_GENERAL1_SMALL"
    image                       = "aws/codebuild/amazonlinux2-x86_64-standard:4.0"
    type                        = "LINUX_CONTAINER"
    image_pull_credentials_type = "CODEBUILD"
  }

  logs_config {
    cloudwatch_logs {
      group_name  = "${var.project_name}-codebuild"
      stream_name = "${var.project_name}-codebuild"
    }

    s3_logs {
      status   = "ENABLED"
      location = "${data.aws_ssm_parameter.codebuild_logs_bucket_id.value}/build-logs"
    }
  }

  source {
    type            = "GITHUB"
    location        = "https://github.com/macgruber99/sqs-simple-example.git"
    git_clone_depth = 1
    buildspec       = "buildspec.yml"

    git_submodules_config {
      fetch_submodules = true
    }

    # Only need auth block if AWS account not linked or ability to override account
    # level auth required.
    # auth {
    #   type     = "CODECONNECTIONS"
    #   resource = data.aws_ssm_parameter.codeconnections_connection.value
    # }
  }

  source_version = "main"

  tags = local.tags
}

resource "aws_codebuild_webhook" "sqs_simple_example_deploy" {
  project_name = aws_codebuild_project.sqs_simple_example.name
  build_type   = "BUILD"

  filter_group {
    filter {
      type    = "EVENT"
      pattern = "PULL_REQUEST_MERGED"
    }

    filter {
      type    = "BASE_REF"
      pattern = "main"
    }
  }
}
