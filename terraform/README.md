# Cloudwatch log manager

![Test](https://img.shields.io/github/workflow/status/skildops/aws-cw-log-group-manager/test/main?label=Test&style=for-the-badge) ![Checkov](https://img.shields.io/github/workflow/status/skildops/aws-cw-log-group-manager/checkov/main?label=Checkov&style=for-the-badge)

This terraform module will deploy the following services:
- IAM Role
- IAM Role Policy
- CloudWatch Event
- Lambda Function

**Note:** You need to implement [remote backend](https://www.terraform.io/docs/language/settings/backends/index.html) by yourself and is recommended for state management.

## Requirements

| Name | Version |
|------|---------|
| terraform | >= 1.0.0 |
| aws | >= 4.0.0 |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| region | AWS region in which you want to create resources | `string` | `"us-east-1"` | no |
| profile | AWS CLI profile to use as authentication method | `string` | `null` | no |
| access_key | AWS access key to use as authentication method | `string` | `null` | no |
| secret_key | AWS secret key to use as authentication method | `string` | `null` | no |
| session_token | AWS session token to use as authentication method | `string` | `null` | no |
| log_retention_role_name | Name of the IAM role to associate with the log retention lambda function | `string` | `"log-group-retention-manager"` | no |
| log_retention_function_name | Name of the lambda function responsible for updating log retention period | `string` | `"log-group-retention-manager"` | no |
| log_encryption_role_name | Name of the IAM role to associate with the log encryption lambda function | `string` | `"log-group-encryption-manager"` | no |
| log_encryption_function_name | Name of the lambda function responsible for updating/removing encryption config for log groups | `string` | `"log-group-encryption-manager"` | no |
| cron_expression | [CRON expression](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-schedule-expressions.html) to determine how frequently `log retention` and `log encryption` function will be invoked | `string` | `"0 12 * * ? *"` | no |
| lambda_runtime | Lambda runtime to use for both the log retention and encryption function | `string` | `"python3.9"` | no |
| lambda_memory_size | Amount of memory to allocate to both the log retention and encryption function | `number` | `128` | no |
| lambda_timeout | Timeout to set for both the log retention and encryption function | `number` | `10` | no |
| lambda_reserved_concurrent_executions | Amount of reserved concurrent executions for this lambda function. A value of `0` disables lambda from being triggered and `-1` removes any concurrency limitations | `number` | `-1` | no |
| lambda_xray_tracing_mode | Whether to sample and trace a subset of incoming requests with AWS X-Ray. **Possible values:** `PassThrough` and `Active` | `string` | `"PassThrough"` | no |
| lambda_cw_log_group_retention | Number of days to store the logs in a log group. Valid values are: 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653, and 0. To never expire the logs provide 0 | `number` | `90` | no |
| lambda_cw_logs_kms_key_arn | ARN of KMS key to enable SSE for CloudWatch log group that will be used to store logs of both the log retention and encryption function | `string` | `null` | no |
| tags | Key value pair to assign to resources | `map(string)` | `{}` | no |
| aws_regions | List of regions within which log group retention period needs to be updated | `list(string)` | `[]` | no |
| log_retention_days | Retention period to be set for all the log groups in the region(s) specified in `aws_regions` | `number` | `90` | no |
| log_encryption_config | To update/remove the KMS key for log group(s) use the following format:<pre>{<br>  us-east-1  = "" # Leave blank to remove KMS key from all the cloudwatch log groups in the particular region<br>  eu-west-1  = "arn:aws:kms:eu-west-1:ACCOUNT_ID:key/xxxxxx"<br>  ap-south-1 = "arn:aws:kms:ap-south-1:ACCOUNT_ID:key/xxxxxx"<br>}</pre> | `map(string)` | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| log_retention_function_name | Name of lambda function created to update retention period for log groups |
| log_encryption_function_name | Name of lambda function created to update/remove KMS key for log groups |
| cron_expression | Interval at which `log retention` and `log encryption` function will be invoked |
