# A Simple SQS Example

A simple example of how to implement Lambda functions for SQS producers and consumers.

## Architecture

![Architecture Diagram](img/architecture-diagram.png)

1. Files are uploaded to an input S3 bucket.
2. An S3 notification triggers the execution of the producer Lambda function.
3. The producer Lambda function processes the S3 object and writes a message to the SQS queue.
4. A Lambda trigger causes the consumer Lambda function execution when a message is put on the queue.
5. The consumer Lambda function processes the message and writes an S3 object to the output bucket.

A DLQ has been configured for the SQS queue.

CloudWatch alarms are deployed to monitor the Lambda functions and SQS queues.

## Poetry

Poetry is used to manage Python dependencies for the Lambda functions.

## Pytest

Pytests tests have been configured for the Lambdas.

## Terraform

The AWS resources are deployed via Terraform.

## CI/CD

TBD

## Go Task

Go Task tasks have been configured to handle the execution of routine commands.

## Pre-commit

Pre-commit hooks have been configured, but need to be installed before they take effect.

## Utility Scripts

The `scripts/write-to-s3.py` script allows for quick creation and uploading of JSON files to the input S3 bucket.
