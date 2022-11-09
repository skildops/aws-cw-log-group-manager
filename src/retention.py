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
LOG_RETENTION_DAYS = int(os.environ.get('LOG_RETENTION_DAYS', 90))
# ==================================

def fetch_active_regions():
    ec2 = boto3.client('ec2', 'us-east-1')
    activeRegions = ec2.describe_regions()['Regions']
    return [r['RegionName'] for r in activeRegions]

def fetch_all_log_groups(cwRegion):
    logGroups = []
    reqArg = {}

    try:
        logs = boto3.client('logs', cwRegion)
        while True:
            logger.info('[{}] Fetching all the log groups available in the region...'.format(cwRegion))

            resp = logs.describe_log_groups(**reqArg)
            logGroups.extend([lg['logGroupName'] for lg in resp['logGroups']])

            if 'nextToken' in resp:
                reqArg['nextToken'] = resp['nextToken']
            else:
                break
        logger.info('[{}] Retention period will be update for the following log groups: {}'.format(cwRegion, logGroups))
    except (ClientError, Exception) as ce:
        logger.error('[{}] Unable to fetch log groups. Reason: {}'.format(cwRegion, ce))

    return {
        cwRegion: logGroups
    }

def update_retention_period(logGroups, awsRegion):
    logGroupResult = {
        'success': 0,
        'failed': 0
    }

    logs = boto3.client('logs', awsRegion)
    for lg in logGroups:
        try:
            logs.put_retention_policy(
                logGroupName=lg,
                retentionInDays=LOG_RETENTION_DAYS
            )

            logGroupResult['success'] += 1

            logger.info('[{}] Retention period updated for {}'.format(awsRegion, lg))
        except (ClientError, Exception) as ce:
            logGroupResult['failed'] += 1
            logger.error('[{}] Unable to update retention period for {}. Reason: {}'.format(awsRegion, lg, ce))

    return {
        awsRegion: logGroupResult
    }

def main():
    if AWS_REGIONS.lower() == 'all':
        cwRegions = fetch_active_regions()
    elif ',' in AWS_REGIONS:
        cwRegions = [r.strip() for r in AWS_REGIONS.split(',')]
    else:
        cwRegions = [AWS_REGIONS]

    if AWS_REGIONS.lower() != 'all':
        validRegions = fetch_active_regions()
        for r in cwRegions:
            if r not in validRegions:
                logger.error('{} is an invalid region hence will be ignored'.format(r))
                cwRegions.remove(r)

    # Fetching all log groups from all the regions
    with concurrent.futures.ThreadPoolExecutor(10) as executor:
        results = [executor.submit(fetch_all_log_groups, r) for r in cwRegions]

    logGroups = {}
    for f in concurrent.futures.as_completed(results):
        logGroups = {**logGroups, **f.result()}

    logger.info('Updating cloudwatch log group retention policy in the following regions: {}'.format(cwRegions))
    with concurrent.futures.ThreadPoolExecutor(10) as executor:
        results = [executor.submit(update_retention_period, logGroups[k], k) for k in logGroups]

    logGroupsResult = {}
    for f in concurrent.futures.as_completed(results):
        logGroupsResult = {**logGroupsResult, **f.result()}

    logger.info('\n=================')
    logger.info('Final Result')
    logger.info('=================')
    logger.info('Regions processed: {}'.format(len(cwRegions)))
    logger.info('------------------------------')
    logger.info('Region ID\tSuccess\tFailed')
    logger.info('------------------------------')
    for k, v in logGroupsResult.items():
        logger.info('{}\t{}\t{}'.format(k, v['success'], v['failed']))

def handler(event, context):
    main()
