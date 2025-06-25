# Lambda SQS Producer

An AWS Lambda function that writes messages to an SQS queue.

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

## Invoking Producer Lambda Function

Typically Lambda functions are triggered by events.  Since the producer function has no event trigger, it needs to be invoked manually in the AWS console or by executing the following:

```bash
aws lambda invoke --function-name sqs-simple-example-producer sqs-simple-example-producer.out
```
