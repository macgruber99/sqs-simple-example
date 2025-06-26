locals {
  buckets = toset(["input", "output"])

  ssm_param_path_queue_url = "/${var.project_name}/queue-url"

  # With merge(), if the same key is defined in both dictionaries, then the one
  # that is later in the argument sequence takes precedence.  Since the Project
  # tag should always be present, it is placed last in the merge() call.
  tags = merge(
    var.additional_tags,
    {
      "Project" = var.project_name,
    }
  )
}
