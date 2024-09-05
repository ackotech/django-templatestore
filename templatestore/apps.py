from django.apps import AppConfig
from templatestore import app_settings
import threading

from templatestore.sqs_consumer import start_consumer_threads


class TemplateStoreAppConfig(AppConfig):
    name = "templatestore"
    def ready(self):
        # Start the periodic task in a new thread
        num_threads = getattr(app_settings, "SQS_LISTENER_THREAD_COUNT", 1)
        thread = threading.Thread(target=start_consumer_threads, args=[num_threads])
        thread.start()
        