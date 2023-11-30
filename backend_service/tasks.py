import logging
import time

from celery import shared_task

@shared_task(ignore_result=False)
def send_register_email(username) -> str:
    time.sleep(3)
    logging.info("User {} registered successfully")