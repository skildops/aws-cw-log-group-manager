## aws-cw-log-group-manager

![License](https://img.shields.io/github/license/skildops/aws-cw-log-group-manager?style=for-the-badge) ![CodeQL](https://img.shields.io/github/workflow/status/skildops/aws-cw-log-group-manager/codeql/main?label=CodeQL&style=for-the-badge) ![Commit](https://img.shields.io/github/last-commit/skildops/aws-cw-log-group-manager?style=for-the-badge) ![Release](https://img.shields.io/github/v/release/skildops/aws-cw-log-group-manager?style=for-the-badge)

### Prerequisites:
- [Terraform](https://www.terraform.io/downloads.html)
- [AWS CLI](https://aws.amazon.com/cli/)

### AWS Services Managed:
- CloudWatch Log Group

### Supported Operations:
- Update retention period
- Update/remove KMS key

### Logic Flow:
![aws-cw-log-group-manager](aws-cw-log-group-manager.jpg "AWS CloudWatch Log Group Manager")

- CloudWatch Event triggers retention and encryption function periodically.
- Retention function scans all the log groups present in the provided region(s) and updates the retention period for all the available log group(s)
- Encryption function scans all the log groups present in the provided region(s) and updates or removes KMS encryption for all the available log group(s)

### Setup:
- Use the [terraform module](terraform) included in this repo to create all the AWS resources required to automate IAM key rotation
