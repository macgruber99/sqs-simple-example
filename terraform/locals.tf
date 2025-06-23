locals {
  ssm_param_path_queue_url = "/${var.project_name}/queue-url"
  ssm_param_path_bucket_name = "/${var.project_name}/s3-bucket-name"

  # With merge(), if the same key is defined in both dictionaries, then the one
  # that is later in the argument sequence takes precedence.
  tags = merge(
    var.additional_tags,
    {
      "Project" = var.project_name,
    }
  )
}
