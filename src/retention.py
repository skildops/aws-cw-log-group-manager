import boto3
import logging
import os
import concurrent.futures

from botocore.exceptions import ClientError

logger = logging.getLogger('retention')
logger.setLevel(logging.INFO)

# ======== Global variables ========
# AWS_REGION environment variable is by default available within lambda environment
AWS_REGIONS = os.environ.get('AWS_REGIONS', os.environ.get('AWS_REGION'))

# No. of days to retain logs within a cloudwatch group
LOG_RETENTION_DAYS = os.environ.get('LOG_RETENTION_DAYS', 90)
# ==================================

def fetch_active_regions():
    ec2 = boto3.client('ec2', 'us-east-1')
    activeRegions = ec2.describe_regions()['Regions']
    return [r['RegionName'] for r in activeRegions]

def validate_aws_regions(regions):
    print('Validating regions...')
    validRegions = fetch_active_regions()
    for r in regions:
        if r not in validRegions:
            return r

    return 'ok'

def update_retention_period(logGroupName, awsRegion):
    try:
        logs = boto3.client('logs', awsRegion)
        logs.put_retention_policy(
            logGroupName=logGroupName,
            retentionInDays=LOG_RETENTION_DAYS
        )
        print('[{}] Retention period updated for {}'.format(awsRegion, logGroupName))
    except (ClientError, Exception) as ce:
        print('[{}] Unable to update retention period for {}. Reason: {}'.format(awsRegion, logGroupName, ce))

def fetch_cw_log_groups(cwRegion):
    logGroups = []
    reqArg = {}

    try:
        logs = boto3.client('logs', cwRegion)
        while True:
            resp = logs.describe_log_groups(**reqArg)
            logGroups.extend([lg['logGroupName'] for lg in resp['logGroups']])

            if 'nextToken' in resp:
                reqArg['nextToken'] = resp['nextToken']
            else:
                break
    except (ClientError, Exception) as ce:
        print('Unable to fetch log groups in {} region. Reason: {}'.format(cwRegion, ce))

    return logGroups

def main():
    if AWS_REGIONS.lower() == 'all':
        cwRegions = fetch_active_regions()
    elif ',' in AWS_REGIONS:
        cwRegions = [r.strip() for r in AWS_REGIONS.split(',')]
    else:
        cwRegions = [AWS_REGIONS]

    if AWS_REGIONS.lower() != 'all':
        isValidRegion = validate_aws_regions(cwRegions)
        if isValidRegion != 'ok':
            print('{} is an invalid region'.format(isValidRegion))
            exit(1)

    print('Updating cloudwatch log group retention policy in following regions: {}'.format(cwRegions))
    for cwRegion in cwRegions:
        logGroups = fetch_cw_log_groups(cwRegion)
        print('[{}] Retention period will be updated for: {}'.format(cwRegion, logGroups))
        with concurrent.futures.ThreadPoolExecutor(min(len(cwRegions), 10)) as executor:
            [executor.submit(update_retention_period, logGroup, cwRegion) for logGroup in logGroups]

def handler(event, context):
    main()

handler(None, None)
