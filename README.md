## aws-cw-log-group-manager

![License](https://img.shields.io/github/license/skildops/aws-cw-log-group-manager?style=for-the-badge) ![CodeQL](https://img.shields.io/github/workflow/status/skildops/aws-cw-log-group-manager/codeql/main?label=CodeQL&style=for-the-badge) ![Commit](https://img.shields.io/github/last-commit/skildops/aws-cw-log-group-manager?style=for-the-badge) ![Release](https://img.shields.io/github/v/release/skildops/aws-cw-log-group-manager?style=for-the-badge)

### Prerequisites:
- [Terraform](https://www.terraform.io/downloads.html)
- [AWS CLI](https://aws.amazon.com/cli/)

### AWS Services Involved:
- CloudWatch Log Group

### Supported Operations:
- Update retention period
- Update KMS key

### Setup:
- Use the [terraform module](terraform) included in this repo to create all the AWS resources required to automate IAM key rotation
- Add the following tags to the IAM user whose access key pair generation needs to be automated. All the tags mentioned are **case-insensitive**:
  - Required:
    - `IKR:EMAIL`: Email address of IAM user where alerts related to access keys will be sent
  - Optional:
    - `IKR:ROTATE_AFTER_DAYS`: After how many days new access key should be generated. **Note:** If you want to control key generation period per user add this tag to the user else environment variable `ROTATE_AFTER_DAYS` will be used
    - `IKR:DELETE_AFTER_DAYS`: After how many days existing access key should be deleted. **Note:** If you want to control key deletion period per user add this tag to the user else environment variable `DELETE_AFTER_DAYS` will be used
    - `IKR:INSTRUCTION_0`: Add help instruction related to updating access key. This instruction will be sent to IAM user whenever a new key pair is generated. **Note:** As AWS restricts [tag value](https://docs.aws.amazon.com/general/latest/gr/aws_tagging.html#tag-conventions) to 256 characters you can use multiple instruction tags by increasing the number (`IKR:INSTRUCTION_0`, `IKR:INSTRUCTION_1` , `IKR:INSTRUCTION_2` and so on). All the instruction tags value will be combined and sent as a single string to the user.
