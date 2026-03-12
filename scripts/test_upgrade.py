import datetime
import logging

logging.basicConfig(filename='logs/assistant.log', level=logging.INFO, format='%(asctime)s - %(message)s')

def log_line(msg):
    logging.info(msg)