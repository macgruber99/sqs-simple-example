config {
  format = "compact"
  force = false

  disabled_by_default = false
}

rule "terraform_typed_variables" {
  enabled = true
}

rule "terraform_unused_declarations" {
  enabled = true
}

rule "terraform_deprecated_index" {
  enabled = true
}

rule "terraform_required_providers" {
  enabled = true
}
