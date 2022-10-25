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

def fetch_all_log_groups(awsRegion):
    logs = boto3.client('logs', awsRegion)
    logGroupNames = []
    reqParams = {}
    
    while True:
        try:
            logger.info('[{}] Fetching all the log groups available in the region...'.format(awsRegion))
            resp = logs.describe_log_groups(**reqParams)

            for lg in resp['logGroups']:
                logGroupNames.append(lg['logGroupName'])

            if 'nextToken' in resp:
                reqParams['nextToken'] = resp['nextToken']
            else:
                break
            
            logger.info('[{}] Encryption config will be updated for the following log groups: {}'.format(awsRegion, logGroupNames))
        except (ClientError, Exception) as ce:
            logger.error('[{}] Unable to fetch log groups. Reason: {}'.format(awsRegion, ce))
    
    return {
        awsRegion: logGroupNames
    }

def update_encryption_key(awsRegion, kmsKeyArn, logGroupNames):
    logGroupResult = {
        'success': 0,
        'failed': 0
    }

    try:
        logs = boto3.client('logs', awsRegion)
        for lg in logGroupNames:
            logger.info('[{}] Updating encryption key for {}...'.format(awsRegion, lg))
            logs.associate_kms_key(
                logGroupName=lg,
                kmsKeyId=kmsKeyArn
            )

            logGroupResult['success'] += 1

            logger.info('[{}] Encryption key updated for log group: {}'.format(awsRegion, lg))
    except (ClientError, Exception) as ce:
        logGroupResult['failed'] += 1
        logger.error('[{}] Unable to update encryption key for {}. Reason: {}'.format(awsRegion, lg, ce))
    
    return {
        awsRegion: logGroupResult
    }


def main():
    validRegions = fetch_active_regions()
    for k, _ in ENCRYPTION_CONFIG:
        if k not in validRegions:
            logger.error('{} is an invalid region hence will be ignored'.format(k))
            ENCRYPTION_CONFIG.pop(k)
    
    # Fetching all log groups from all the regions
    with concurrent.futures.ThreadPoolExecutor(10) as executor:
        results = [executor.submit(fetch_all_log_groups, r) for r, _ in ENCRYPTION_CONFIG]
    
    logGroups = {}
    for f in concurrent.futures.as_completed(results):
        logGroups = {**logGroups, **f.result()}

    # Updating encryption key for all log groups
    with concurrent.futures.ThreadPoolExecutor(10) as executor:
        results = [executor.submit(update_encryption_key, r, ENCRYPTION_CONFIG[r], logGroups[r]) for r, _ in ENCRYPTION_CONFIG]
    
    logGroupsResult = {}
    for f in concurrent.futures.as_completed(results):
        logGroupsResult = {**logGroupsResult, **f.result()}
    
    logger.info('=================')
    logger.info('Result:')
    logger.info('=================')
    logger.info('Regions processed: {}'.format(len(ENCRYPTION_CONFIG)))
    logger.info('Region\tSuccess\tFailed')
    for k, v in logGroupsResult:
        logger.info('{}\t{}\t{}'.format(k, v['success'], v['failed']))

def handler(event, context):
    main()

handler(None, None)
