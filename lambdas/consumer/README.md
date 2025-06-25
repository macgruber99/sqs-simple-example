# Lambda SQS Consumer

An AWS Lambda function that reads messages from an SQS queue and writes them to an S3 bucket.

## Building a Package

A new package needs to be built before running the Terraform code to update the Lambda function.

Use the `poetry-plugin-lambda-build` plugin to build a new package by executing the following:

```bash
poetry build-lambda
```

## Running Unit Tests

To run unit tests, execute the following:

```bash
poetry run pytest
```
