import boto3
import logging
import os
import concurrent.futures

from botocore.exceptions import ClientError

logger = logging.getLogger('encryption')
logger.setLevel(logging.INFO)

# ======== Global variables ========
# AWS_REGION environment variable is by default available within lambda environment
AWS_REGIONS = os.environ.get('AWS_REGIONS', os.environ.get('AWS_REGION'))

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
            print('{} if an invalid region'.format(isValidRegion))
            exit(1)

def handler(event, context):
    main()

handler(None, None)
