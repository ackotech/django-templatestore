import logging
import boto3

MAX_NO_OF_MSG = 2
MAX_WAIT_TIME = 20
DEFAULT_VISIBILITY_TIMEOUT = 60
REGION = "ap-south-1"

sqs_client = boto3.client("sqs", region_name=REGION)
logger = logging.getLogger(__name__)


class SqsReader:
    def __init__(
        self,
        queue_url,
        max_no_of_msg=MAX_NO_OF_MSG,
        wait_time_seconds=MAX_WAIT_TIME,
        visibility_timeout=DEFAULT_VISIBILITY_TIMEOUT,
    ):
        self.wait_time_seconds = min(wait_time_seconds, MAX_WAIT_TIME)
        self.max_no_of_msg = min(max_no_of_msg, MAX_NO_OF_MSG)
        self.queue_url = queue_url
        self.visibility_timeout = visibility_timeout

    def __iter__(self):
        self.messages = []
        return self

    def __next__(self):
        if len(self.messages) == 0:
            try:
                response = sqs_client.receive_message(
                    QueueUrl=self.queue_url,
                    WaitTimeSeconds=self.wait_time_seconds,
                    MaxNumberOfMessages=self.max_no_of_msg,
                    VisibilityTimeout=self.visibility_timeout,
                    MessageAttributeNames=["All"],
                )
                self.messages = response.get("Messages", [])
            except Exception:
                logger.exception(
                    "Error receiving messages from SQS queue: %s" % self.queue_url
                )
                # newrelic.agent.notice_error()
        if len(self.messages) == 0:
            raise StopIteration
        return self.messages.pop()


def delete_message(queue_url, receipt_handle):
    print("In delete message")
    try:
        response = sqs_client.delete_message(
            QueueUrl=queue_url, ReceiptHandle=receipt_handle
        )
        print("Deleted message from queue -> ", response)
        logger.info("Deleted message from queue -> ", response)
    except Exception as ex:
        logger.exception("Failed to delete message", error=str(ex))
        raise SqsException("Failed to delete message")


class SqsException(Exception):
    pass