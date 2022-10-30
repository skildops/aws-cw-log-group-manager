output "log_retention_function_name" {
  value       = aws_lambda_function.log_retention.function_name
  description = "Name of lambda function created to update retention period for log groups"
}

output "log_encryption_function_name" {
  value       = aws_lambda_function.log_encryption.function_name
  description = "Name of lambda function created to update/remove KMS key for log groups"
}

output "cron_expression" {
  value       = aws_cloudwatch_event_rule.log_retention.schedule_expression
  description = "Interval at which `log retention` and `log encryption` function will be invoked"
}
