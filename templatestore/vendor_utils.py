# views.py
import logging
import json
import boto3
import time
import threading

from templatestore import app_settings as ts_settings
logger = logging.getLogger(__name__)

TEMPLATE_SYNC_SQS = ts_settings.TEMPLATE_SYNC_SQS

# Create a session using the specified profile
session = boto3.Session(profile_name="ackodev")

# Create an SQS client using the session
sqs = session.client('sqs', region_name='ap-south-1')
# sqs = boto3.client('sqs', region_name='ap-south-1')

def send_message(message_body, message_attributes=None):
    """
    Send a message to an Amazon SQS queue.

    :param queue: The queue that receives the message.
    :param message_body: The body text of the message.
    :param message_attributes: Custom attributes of the message. These are key-value
                               pairs that can be whatever you want.
    :return: The response from SQS that contains the assigned message ID.
    """

    
    # sqs = boto3.client('sqs', region_name='ap-south-1')
    # queue_url = "https://sqs.ap-south-1.amazonaws.com/663498825379/platform-ackommunication-email-p2"
    
    if not message_attributes:
        message_attributes = {}

    try:
        response = sqs.send_message(
            QueueUrl=TEMPLATE_SYNC_SQS,
            MessageBody=json.dumps(message_body), 
            MessageAttributes=message_attributes
        )
    except Exception as error:
        print("Send message failed: %s", message_body)
        raise error
    else:
        return response

def receive_messages(queue, max_number):
    """
    Receive a batch of messages in a single request from an SQS queue.

    :param queue: The queue from which to receive messages.
    :param max_number: The maximum number of messages to receive. The actual number
                       of messages received might be less.
    :return: The list of Message objects received. These each contain the body
             of the message and metadata and custom attributes.
    """
    try:
        messages = queue.receive_messages(
            MessageAttributeNames=["All"],
            MaxNumberOfMessages=1
        )
        for msg in messages:
            logger.info("Received message: %s: %s", msg.message_id, msg.body)
    except Exception as error:
        logger.exception("Couldn't receive messages from queue: %s", queue)
        raise error
    else:
        print(messages)
        return messages

def periodic_task():
    while True:
        # Your task logic here
        print("Periodic task running...")
        time.sleep(10)