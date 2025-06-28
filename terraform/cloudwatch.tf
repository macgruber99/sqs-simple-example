resource "aws_cloudwatch_metric_alarm" "dlq_new_message" {
  alarm_name          = "DLQ-new-message"
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
