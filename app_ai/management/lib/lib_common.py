# -*- coding: utf-8 -*-
"""
  Call API via rabbitmq
"""
import requests


def send_response(logger, status_url, status_data):
    """
    ステータスとログをサーバーへ送信

    :param logger:
    :param status_url:
    :param status_data:
    :return:
    """
    logger.info("Send status.")
    # status & log
    response = requests.post(status_url, status_data)
    logger.info("response: code: %d, text: %s" % (response.status_code, response.text))


