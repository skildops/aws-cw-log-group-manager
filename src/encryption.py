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

def main():
    validRegions = fetch_active_regions()
    for k, _ in ENCRYPTION_CONFIG:
        if k not in validRegions:
            print('{} is an invalid region'.format(k))
            exit(1)
    return True

def handler(event, context):
    main()

handler(None, None)
