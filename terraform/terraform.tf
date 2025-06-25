terraform {
  required_version = ">= 1.9.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket       = "***REMOVED***"
    key          = "sqs-simple-example/terraform.tfstate"
    region       = "us-west-2"
    encrypt      = true
    use_lockfile = true # S3 native locking
  }
}
