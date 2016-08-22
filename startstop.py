#!/usr/bin/python

import boto
import boto.ec2
import time
import datetime

# log
import logging
logger = logging.getLogger('startstop')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(name)s %(asctime)s [%(levelname)s] %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

boto_logger = logging.getLogger('boto')
boto_logger.setLevel(logging.INFO)
boto_logger.addHandler(ch)

#
START_HOUR=7
STOP_HOUR=18
debug_flag=False

# we'll be working with starttime in UTC
current_time = datetime.datetime.utcnow()

def check_resource(resource_offset):
    # process the time from offset
    delta = datetime.timedelta(hours= int(resource_offset) )
    offset_time = current_time + delta
    
    if offset_time.weekday() in [ 5, 6 ]:
        # don't run on weekends
        return 0

    if offset_time.hour >= START_HOUR and offset_time.hour < STOP_HOUR:
        return 1
    else:
        return 0

def ec2_handler():
    ec2_connection = boto.ec2.connect_to_region('eu-central-1')
    instance_list = ec2_connection.get_only_instances()

    stop_list = []
    start_list = []

    for instance in instance_list:
        logger.debug('Processing instance {0}'.format(instance.id))
        if 'Nightly' in instance.tags:
            resource_offset = instance.tags.get('Nightly')
            should_run = check_resource(resource_offset)
            if instance.state == 'stopped' and should_run:
                start_list.append(instance.id)
                logger.debug('Adding instance {0} to start list'.format(instance.id))
            if instance.state == 'running' and not should_run:
                stop_list.append(instance.id)
                logger.debug('Adding instance {0} to stop list'.format(instance.id))

    if len(stop_list) > 0:
        logger.info('Stopping instances: {0}'.format(stop_list))
        ec2_connection.stop_instances(instance_ids=stop_list, dry_run=debug_flag)
    else:
        logger.info('No instances to stop')

    if len(start_list) > 0:
        logger.info('Starting instances: {0}'.format(start_list))
        ec2_connection.start_instances(instance_ids=start_list, dry_run=debug_flag)
    else:
        logger.info('No instances to start')


# lambda
def lambda_handler(event, context):
    ec2_handler()

# add direct exec ability for testing
if __name__ == '__main__':
    ec2_handler()