data "aws_caller_identity" "current" {}

locals {
  account_id           = data.aws_caller_identity.current.account_id
  lambda_assume_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow"
    }
  ]
}
EOF
}

# ====== log-retention ======
resource "aws_iam_role" "log_retention" {
  name                  = var.log_retention_role_name
  assume_role_policy    = local.lambda_assume_policy
  force_detach_policies = true
  tags                  = var.tags
}

data "aws_iam_policy_document" "log_retention_policy" {
  # checkov:skip=CKV_AWS_111: Write access required
  statement {
    effect = "Allow"
    actions = [
      "ec2:DescribeRegions",
      "logs:DescribeLogGroups",
      "logs:PutRetentionPolicy"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "log_retention_policy" {
  name   = var.log_retention_role_name
  role   = aws_iam_role.log_retention.id
  policy = data.aws_iam_policy_document.log_retention_policy.json
}

resource "aws_iam_role_policy_attachment" "log_retention_logs" {
  role       = aws_iam_role.log_retention.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_cloudwatch_event_rule" "log_retention" {
  name                = "UpdateLogRetention"
  description         = "Triggers a lambda function periodically which updates retention period of all log groups"
  is_enabled          = length(var.aws_regions) > 1 ? true : false
  schedule_expression = "cron(${var.cron_expression})"
}

resource "aws_cloudwatch_event_target" "log_retention" {
  rule      = aws_cloudwatch_event_rule.log_retention.name
  target_id = "TriggerUpdateLogRetentionLambda"
  arn       = aws_lambda_function.log_retention.arn
}

resource "aws_lambda_permission" "log_retention" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.log_retention.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.log_retention.arn
}

resource "aws_cloudwatch_log_group" "log_retention" {
  name              = "/aws/lambda/${var.log_retention_function_name}"
  retention_in_days = var.lambda_cw_log_group_retention
  kms_key_id        = var.lambda_cw_logs_kms_key_arn
  tags              = var.tags
}

resource "aws_lambda_function" "log_retention" {
  # checkov:skip=CKV_AWS_50: Enabling X-Ray tracing depends on user
  # checkov:skip=CKV_AWS_115: Setting reserved concurrent execution depends on user
  # checkov:skip=CKV_AWS_116: DLQ not required
  # checkov:skip=CKV_AWS_117: VPC deployment not required
  # checkov:skip=CKV_AWS_173: By default environment variables are encrypted at rest
  # checkov:skip=CKV_AWS_272: Code signing not required
  function_name    = var.log_retention_function_name
  description      = "Update log group retention period"
  role             = aws_iam_role.log_retention.arn
  filename         = data.archive_file.retention.output_path
  source_code_hash = data.archive_file.retention.output_base64sha256
  handler          = "retention.handler"
  runtime          = var.lambda_runtime

  memory_size                    = var.lambda_memory_size
  timeout                        = var.lambda_timeout
  reserved_concurrent_executions = var.lambda_reserved_concurrent_executions

  tracing_config {
    mode = var.lambda_xray_tracing_mode
  }

  environment {
    variables = {
      AWS_REGIONS        = join(", ", var.aws_regions)
      LOG_RETENTION_DAYS = var.log_retention_days
    }
  }

  tags = var.tags
}

# ====== log-encryption ======
resource "aws_iam_role" "log_encryption" {
  name                  = var.log_encryption_role_name
  assume_role_policy    = local.lambda_assume_policy
  force_detach_policies = true
  tags                  = var.tags
}

data "aws_iam_policy_document" "log_encryption_policy" {
  # checkov:skip=CKV_AWS_111: Write access required
  statement {
    effect = "Allow"
    actions = [
      "ec2:DescribeRegions",
      "logs:DescribeLogGroups",
      "logs:AssociateKmsKey",
      "logs:DisassociateKmsKey"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "log_encryption_policy" {
  name   = var.log_encryption_role_name
  role   = aws_iam_role.log_encryption.id
  policy = data.aws_iam_policy_document.log_encryption_policy.json
}

resource "aws_iam_role_policy_attachment" "log_encryption_logs" {
  role       = aws_iam_role.log_encryption.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_cloudwatch_event_rule" "log_encryption" {
  name                = "UpdateLogEncryption"
  description         = "Triggers a lambda function periodically which updates/removes KMS key for all log groups"
  is_enabled          = length(var.log_encryption_config) > 1 ? true : false
  schedule_expression = "cron(${var.cron_expression})"
}

resource "aws_cloudwatch_event_target" "log_encryption" {
  rule      = aws_cloudwatch_event_rule.log_encryption.name
  target_id = "TriggerUpdateLogEncryptionLambda"
  arn       = aws_lambda_function.log_encryption.arn
}

resource "aws_lambda_permission" "log_encryption" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.log_encryption.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.log_encryption.arn
}

resource "aws_cloudwatch_log_group" "log_encryption" {
  name              = "/aws/lambda/${var.log_encryption_function_name}"
  retention_in_days = var.lambda_cw_log_group_retention
  kms_key_id        = var.lambda_cw_logs_kms_key_arn
  tags              = var.tags
}

resource "aws_lambda_function" "log_encryption" {
  # checkov:skip=CKV_AWS_50: Enabling X-Ray tracing depends on user
  # checkov:skip=CKV_AWS_115: Setting reserved concurrent execution depends on user
  # checkov:skip=CKV_AWS_116: DLQ not required
  # checkov:skip=CKV_AWS_117: VPC deployment not required
  # checkov:skip=CKV_AWS_173: By default environment variables are encrypted at rest
  # checkov:skip=CKV_AWS_272: Code signing not required
  function_name    = var.log_encryption_function_name
  description      = "Update/Remove KMS key for log group"
  role             = aws_iam_role.log_encryption.arn
  filename         = data.archive_file.encryption.output_path
  source_code_hash = data.archive_file.encryption.output_base64sha256
  handler          = "encryption.handler"
  runtime          = var.lambda_runtime

  memory_size                    = var.lambda_memory_size
  timeout                        = var.lambda_timeout
  reserved_concurrent_executions = var.lambda_reserved_concurrent_executions

  tracing_config {
    mode = var.lambda_xray_tracing_mode
  }

  environment {
    variables = {
      LOG_ENCRYPTION_CONFIG = jsonencode(var.log_encryption_config)
    }
  }

  tags = var.tags
}
