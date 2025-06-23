# Lambda SQS Producer

An AWS Lambda function that writes messages to an SQS queue.

## Building a Package

A new package needs to be built before running the Terraform code to update the Lambda function.

Use the `poetry-plugin-lambda-build` plugin to build a new package by executing the following:

```bash
poetry build-lambda
```

## Invoking Producer Lambda Function


```bash
aws lambda invoke --function-name sqs-simple-example-producer sqs-simple-example-producer.out
```
