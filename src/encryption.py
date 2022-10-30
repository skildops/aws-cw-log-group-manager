import boto3
import logging
import os
import json
import concurrent.futures

from botocore.exceptions import ClientError

logger = logging.getLogger('encryption')
logging.getLogger().addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

# ======== Global variables ========
'''
LOG_ENCRYPTION_CONFIG structure:
{
    "ap-south-1": "KMS_KEY_ARN",
    "us-east-1": "KMS_KEY_ARN",
    "eu-west-1": "" # Leave blank to remove KMS key from all the cloudwatch log groups in the particular region
}
'''
LOG_ENCRYPTION_CONFIG = json.loads(os.environ.get('LOG_ENCRYPTION_CONFIG', {}))

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
        'type': 'remove' if kmsKeyArn == '' else 'add',
        'success': 0,
        'failed': 0
    }

    logs = boto3.client('logs', awsRegion)
    for lg in logGroupNames:
        try:
            logger.info('[{}] {} encryption key for {}...'.format(awsRegion, 'Removing' if kmsKeyArn == '' else 'Updating', lg))

            if kmsKeyArn == "":
                logs.disassociate_kms_key(
                    logGroupName=lg
                )
            else:
                logs.associate_kms_key(
                    logGroupName=lg,
                    kmsKeyId=kmsKeyArn
                )

            logger.info('[{}] Encryption key {} for log group: {}'.format(awsRegion, 'removed' if kmsKeyArn == '' else 'updated', lg))
            logGroupResult['success'] += 1
        except (ClientError, Exception) as ce:
            logGroupResult['failed'] += 1
            logger.error('[{}] Unable to update encryption key for {}. Reason: {}'.format(awsRegion, lg, ce))

    return {
        awsRegion: logGroupResult
    }


def main():
    validRegions = fetch_active_regions()
    for k in LOG_ENCRYPTION_CONFIG:
        if k not in validRegions:
            logger.error('{} is an invalid region hence will be ignored'.format(k))
            LOG_ENCRYPTION_CONFIG.pop(k)

    # Fetching all log groups from all the regions
    with concurrent.futures.ThreadPoolExecutor(10) as executor:
        results = [executor.submit(fetch_all_log_groups, r) for r in LOG_ENCRYPTION_CONFIG]

    logGroups = {}
    for f in concurrent.futures.as_completed(results):
        logGroups = {**logGroups, **f.result()}

    # Updating encryption key for all log groups
    with concurrent.futures.ThreadPoolExecutor(10) as executor:
        results = [executor.submit(update_encryption_key, region, LOG_ENCRYPTION_CONFIG[region], logGroups[region]) for region in LOG_ENCRYPTION_CONFIG]

    logGroupsResult = {}
    for f in concurrent.futures.as_completed(results):
        logGroupsResult = {**logGroupsResult, **f.result()}

    logger.info('=================')
    logger.info('Final Result')
    logger.info('=================')
    logger.info('Regions processed: {}'.format(len(LOG_ENCRYPTION_CONFIG)))
    logger.info('\nKMS key update final result:')
    logger.info('------------------------------')
    logger.info('Region ID\tSuccess\tFailed')
    logger.info('------------------------------')
    for k, v in logGroupsResult.items():
        if v['type'] == 'add':
            logger.info('{}\t{}\t{}'.format(k, v['success'], v['failed']))

    logger.info('\nKMS key remove final result:')
    logger.info('------------------------------')
    logger.info('Region ID\tSuccess\tFailed')
    logger.info('------------------------------')
    for k, v in logGroupsResult.items():
        if v['type'] == 'remove':
            logger.info('{}\t{}\t{}'.format(k, v['success'], v['failed']))

def handler(event, context):
    main()

handler(None, None)
