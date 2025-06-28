resource "aws_cloudwatch_metric_alarm" "dlq_new_message" {
  alarm_name          = "${var.project_name}-dlq-new-message"
  alarm_description   = "Alarm when there are new messages in the DLQ"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = "60"
  statistic           = "Sum"
  threshold           = "0"

  dimensions = {
    QueueName = module.sqs.dead_letter_queue_name
  }

  alarm_actions             = [aws_sns_topic.alerts.arn]
  ok_actions                = [aws_sns_topic.alerts.arn]
  insufficient_data_actions = []
}

resource "aws_cloudwatch_metric_alarm" "queue_old_message" {
  alarm_name          = "${var.project_name}-queue-old-message"
  alarm_description   = "Alarm when there are old messages in the queue"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "ApproximateAgeOfOldestMessage"
  namespace           = "AWS/SQS"
  period              = "60"
  statistic           = "Maximum"
  threshold           = "3600" # 1 hour in seconds

  dimensions = {
    QueueName = module.sqs.queue_name
  }

  alarm_actions             = [aws_sns_topic.alerts.arn]
  ok_actions                = [aws_sns_topic.alerts.arn]
  insufficient_data_actions = []
}

resource "aws_cloudwatch_metric_alarm" "lambda_throttle" {
  for_each = toset([
    module.lambda_sqs_producer.lambda_function_name,
    module.lambda_sqs_consumer.lambda_function_name
  ])

  alarm_name          = "${each.key}-lambda-throttle"
  alarm_description   = "Alarm when Lambda function is throttled"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Throttles"
  namespace           = "AWS/Lambda"
  period              = "60"
  statistic           = "Sum"
  threshold           = "0"

  dimensions = {
    FunctionName = each.key
  }

  alarm_actions             = [aws_sns_topic.alerts.arn]
  ok_actions                = [aws_sns_topic.alerts.arn]
  insufficient_data_actions = []
}

# since producer and consumer Lambda function errors result in the message
# being sent to the DLQ, this alarm is in a sense redundant
resource "aws_cloudwatch_metric_alarm" "lambda_error" {
  for_each = toset([
    module.lambda_sqs_producer.lambda_function_name,
    module.lambda_sqs_consumer.lambda_function_name
  ])

  alarm_name          = "${each.key}-lambda-error"
  alarm_description   = "Alarm when Lambda function encounters an error"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "60"
  statistic           = "Sum"
  threshold           = "0"

  dimensions = {
    FunctionName = each.key
  }

  alarm_actions             = [aws_sns_topic.alerts.arn]
  ok_actions                = [aws_sns_topic.alerts.arn]
  insufficient_data_actions = []
}
