import boto3
import logging
import os
import concurrent.futures

from botocore.exceptions import ClientError

logger = logging.getLogger('encryption')
logger.setLevel(logging.INFO)

# ======== Global variables ========
'''
ENCRYPTION_CONFIG structure:
{
    "ap-south-1": "KMS_KEY_ARN",
    "us-east-1": "KMS_KEY_ARN"
}
'''
ENCRYPTION_CONFIG = os.environ.get('ENCRYPTION_CONFIG', {})

def fetch_active_regions():
    ec2 = boto3.client('ec2', 'us-east-1')
    activeRegions = ec2.describe_regions()['Regions']
    return [r['RegionName'] for r in activeRegions]

def fetch_all_log_groups(region):
    logs = boto3.client('logs', region)
    logGroupNames = []
    reqParams = {}
    
    while True:
        try:
            print('[{}] Fetching all the log groups available in the region...'.format(region))
            resp = logs.describe_log_groups(**reqParams)

            for lg in resp['logGroups']:
                logGroupNames.append(lg['logGroupName'])

            if 'nextToken' in resp:
                reqParams['nextToken'] = resp['nextToken']
            else:
                break
        except (ClientError, Exception) as ce:
            print('[{}] Unable to fetch log groups. Reason: {}'.format(region, ce))
    
    return {
        region: logGroupNames
    }

def update_encryption_key(region, kmsKeyArn, logGroupNames):
    logs = boto3.client('logs', region)

    for lg in logGroupNames:
        try:
            print('[{}] Updating encryption key for {}...'.format(region, lg))
            logs.associate_kms_key(
                logGroupName=lg,
                kmsKeyId=kmsKeyArn
            )
        except (ClientError, Exception) as ce:
            print('[{}] Unable to update encryption key for {}. Reason: {}'.format(region, lg, ce))


def main():
    validRegions = fetch_active_regions()
    for k, _ in ENCRYPTION_CONFIG:
        if k not in validRegions:
            print('{} is an invalid region'.format(k))
            exit(1)
    
    # Fetching all log groups from all the regions
    with concurrent.futures.ThreadPoolExecutor(10) as executor:
        results = [executor.submit(fetch_all_log_groups, r) for r, _ in ENCRYPTION_CONFIG]
    
    logGroups = {}
    for f in concurrent.futures.as_completed(results):
        logGroups = {**logGroups, **f.result()}

    # Updating encryption key for all log groups
    with concurrent.futures.ThreadPoolExecutor(10) as executor:
        results = [executor.submit(update_encryption_key, r, ENCRYPTION_CONFIG[r], logGroups[r]) for r, _ in ENCRYPTION_CONFIG]
    
    logGroups = {}
    for f in concurrent.futures.as_completed(results):
        logGroups = {**logGroups, **f.result()}

def handler(event, context):
    main()

handler(None, None)
