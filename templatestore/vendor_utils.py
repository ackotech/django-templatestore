# views.py

import json
import boto3


def send_message(message_body, message_attributes=None):
    """
    Send a message to an Amazon SQS queue.

    :param queue: The queue that receives the message.
    :param message_body: The body text of the message.
    :param message_attributes: Custom attributes of the message. These are key-value
                               pairs that can be whatever you want.
    :return: The response from SQS that contains the assigned message ID.
    """

    # Create a session using the specified profile
    # session = boto3.Session(profile_name="ackodev")
    
    # Create an SQS client using the session
    # sqs = session.client('sqs')
    sqs = boto3.client('sqs')

    # sqs = boto3.client('sqs', region_name='ap-south-1')
    queue_url = "https://sqs.ap-south-1.amazonaws.com/663498825379/platform-ackommunication-email-p2"
    queue_url = "https://sqs.ap-south-1.amazonaws.com/663498825379/central-growth-template-update-sync"
    
    message_body = {"test": "abc"}

    if not message_attributes:
        message_attributes = {}

    try:
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message_body), 
            MessageAttributes=message_attributes
        )
    except Exception as error:
        print("Send message failed: %s", message_body)
        raise error
    else:
        print(response)
        return response
