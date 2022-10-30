variable "region" {
  type        = string
  default     = "us-east-1"
  description = "AWS region in which you want to create resources"
}

variable "profile" {
  type        = string
  default     = null
  description = "AWS CLI profile to use as authentication method"
}

variable "access_key" {
  type        = string
  default     = null
  description = "AWS access key to use as authentication method"
}

variable "secret_key" {
  type        = string
  default     = null
  description = "AWS secret key to use as authentication method"
}

variable "session_token" {
  type        = string
  default     = null
  description = "AWS session token to use as authentication method"
}

variable "log_retention_role_name" {
  type        = string
  default     = "update-log-retention"
  description = "Name for IAM role to assocaite with log retention lambda function"
}

variable "log_retention_function_name" {
  type        = string
  default     = "update-log-retention"
  description = "Name for lambda function responsible for updating log retention period"
}

variable "log_encryption_role_name" {
  type        = string
  default     = "iam-key-destructor"
  description = "Name for IAM role to assocaite with key destructor lambda function"
}

variable "log_encryption_function_name" {
  type        = string
  default     = "iam-key-destructor"
  description = "Name for lambda function responsible for deleting existing access key pair"
}

variable "cron_expression" {
  type        = string
  default     = "0 12 * * ? *"
  description = "[CRON expression](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-schedule-expressions.html) to determine how frequently `key creator` function will be invoked to check if new key pair needs to be generated for an IAM user"
}

variable "lambda_runtime" {
  type        = string
  default     = "python3.9"
  description = "Lambda runtime to use for code execution for both creator and destructor function"
}

variable "lambda_memory_size" {
  type        = number
  default     = 128
  description = "Amount of memory to allocate to both creator and destructor function"
}

variable "lambda_timeout" {
  type        = number
  default     = 10
  description = "Timeout to set for both creator and destructor function"
}

variable "lambda_reserved_concurrent_executions" {
  type        = number
  default     = -1
  description = "Amount of reserved concurrent executions for this lambda function. A value of `0` disables lambda from being triggered and `-1` removes any concurrency limitations"
}

variable "lambda_xray_tracing_mode" {
  type        = string
  default     = "PassThrough"
  description = "Whether to sample and trace a subset of incoming requests with AWS X-Ray. **Possible values:** `PassThrough` and `Active`"
}

variable "lambda_cw_log_group_retention" {
  type        = number
  default     = 90
  description = "Number of days to store the logs in a log group. Valid values are: 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653, and 0. To never expire the logs provide 0"
}

variable "lambda_cw_logs_kms_key_arn" {
  type        = string
  default     = null
  description = "ARN of KMS key to use for encrypting CloudWatch logs at rest"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Key value pair to assign to resources"
}

variable "aws_regions" {
  type        = list(string)
  default     = []
  description = "List of regions within which log group retention period needs to be updated"
}

variable "log_retention_days" {
  type        = number
  default     = 90
  description = "Retention period to be set for all the log groups in the region(s) specified in `aws_regions`"
}

variable "encryption_config" {
  type        = map(string)
  default     = {}
  description = <<-EOT
    To update/remove the KMS key for log group use the following format:
    ```{
      us-east-1  = "" # Leave blank to remove KMS key from all the cloudwatch log groups in the particular region
      eu-west-1  = "arn:aws:kms:eu-west-1:ACCOUNT_ID:key/xxxxxx"
      ap-south-1 = "arn:aws:kms:ap-south-1:ACCOUNT_ID:key/xxxxxx"
    }```
  EOT
}
