resource "aws_codebuild_project" "sqs_simple_example" {
  name          = var.project_name
  description   = "Codebuild project for ${var.project_name}"
  build_timeout = var.codebuild_timeout
  service_role  = aws_iam_role.sqs_simple_example_codebuild.arn

  artifacts {
    type = "NO_ARTIFACTS"
  }

  environment {
    compute_type                = var.codebuild_compute_type
    image                       = var.codebuild_image
    type                        = var.codebuild_env_type
    image_pull_credentials_type = "CODEBUILD"
  }

  logs_config {
    cloudwatch_logs {
      group_name  = "${var.project_name}-codebuild"
      stream_name = "${var.project_name}-codebuild"
    }

    s3_logs {
      status   = "ENABLED"
      location = "${data.aws_ssm_parameter.codebuild_logs_bucket_id.value}/build-logs/${var.project_name}"
    }
  }

  source {
    type            = "GITHUB"
    location        = var.github_repo
    git_clone_depth = 1
    buildspec       = var.buildspec_file

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

  source_version = var.github_source_version

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
      pattern = var.github_source_version
    }
  }
}
