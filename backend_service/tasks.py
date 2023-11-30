import time
import logging

from celery import shared_task


@shared_task(ignore_result=False)
def send_register_email(username) -> str:
    time.sleep(3)
    logging.info("User '{}' registration mail sent successfully.")