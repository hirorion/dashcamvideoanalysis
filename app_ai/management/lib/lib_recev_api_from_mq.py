# -*- coding: utf-8 -*-
"""
  Call API via rabbitmq
"""


def recv_api_action_stop(thread_ctrl, id):
    """
    Check received api command from Django via MQ
    :param thread_ctrl: control command array
    :return: true/false
    """

    ctrl = thread_ctrl[id]
    cmd = ctrl["cmd"]
    if cmd == "stop":
        return True

    return False


def recv_api_action_finish(thread_ctrl, id):
    """
    Check received api command from Django via MQ
    :param thread_ctrl: control command array
    :return: true/false
    """

    ctrl = thread_ctrl[id]
    cmd = ctrl["cmd"]
    if cmd == "finish":
        return True

    return False
