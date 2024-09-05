import time
from concurrent.futures import ThreadPoolExecutor

import json
import logging
import newrelic.agent
from templatestore import sqs_utils
from templatestore import app_settings

from templatestore.sqs_utils import SqsReader

logger = logging.getLogger(__name__)

@newrelic.agent.background_task(group="template_service/async")
def process_async_request():
    for message in SqsReader(queue_url=app_settings.TEMPLATE_SYNC_SQS):
        print("Iterating message")
        try:
            content = json.loads(message.get("Body", "{}"))
            print(content)
            logger.info("Content received in the queue: %s" % content)
            if content == None:
                result = (content)
                if not result.get("success", False):
                    newrelic.agent.record_custom_metric(
                        "Custom/failed_async_request/count", 1
                    )
                    logger.info("Error in ")
                    # update_failure_response_to_client(
                    #     "Error in generating pdf!",
                    #     request_id,
                    #     callback_url,
                    #     result.get("error"),
                    # )
                else:
                    newrelic.agent.record_custom_metric(
                        "Custom/successful_async_request/count", 1
                    )
                    print()
                    sqs_utils.delete_message(
                        queue_url=app_settings.TEMPLATE_SYNC_SQS,
                        receipt_handle=message.get("ReceiptHandle"),
                    )
            else:
                print("Invalid request")
                logger.error(
                    "Invalid request: request_id or callback_url is missing in the request"
                )
                newrelic.agent.record_custom_metric(
                    "Custom/invalid_async_request/count", 1
                )
                sqs_utils.delete_message(
                    queue_url=app_settings.TEMPLATE_SYNC_SQS,
                    receipt_handle=message.get("ReceiptHandle"),
                )
        except Exception as ex:
            logger.error("Something went wrong, error: %s" % str(ex))
            # newrelic.agent.notice_error(attributes={"callback_type": "failure", "callback_url": callback_url})


@newrelic.agent.background_task(group="template_service/async")
def start_consumer_threads(num_threads):
    listener_threads = []
    with ThreadPoolExecutor(
        max_workers=num_threads, thread_name_prefix="consumer-thread-"
    ) as executor:
        for i in range(num_threads):
            listener_threads.append(executor.submit(process_async_request))
        while True:
            time.sleep(1)  # wait for sometime before reiterating
            for i in range(num_threads):
                if listener_threads[i].done():
                    if listener_threads[i].exception():
                        logger.error(
                            "Error while executing thread-%d, error: %s"
                            % (i, listener_threads[i].exception())
                        )
                        newrelic.agent.record_custom_metric(
                            "Custom/consumer_thread_failure/count", 1
                        )
                    listener_threads[i] = executor.submit(process_async_request)
                    logger.info("Restarted listener on thread-%d" % i)