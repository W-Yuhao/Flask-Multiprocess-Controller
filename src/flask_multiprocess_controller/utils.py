# -*- coding: utf-8 -*-
# @author: Yuhao Wang
# @date: 2022/07/19

import json
import logging
import requests
from multiprocessing import Lock
from multiprocessing.connection import Connection

logger = logging.getLogger(__name__)


class AbortException(BaseException):
    """
    Exception raise when receive stop signal when at checkpoint method in BasicTask()
    """
    pass


def safe_pipe_send(lock: Lock, pipe_end: Connection, msg) -> None:
    """
    safely send msg using Pipe between processes by Lock
    :param lock: Lock that both pipes' end used
    :param pipe_end: sending end the Pipe
    :param msg: message to send
    :return:
    """
    lock.acquire()
    try:
        pipe_end.send(msg)
    finally:
        lock.release()


def send_request(url, data, callback_loop: int = 3,
                 callback_header=None, callback_timeout: int = 60):

    if callback_header is None:
        callback_header = {'Content-Type': 'application/json'}
    update_flag = True
    logger.info('alg callback after process')
    logger.info(f'input arguments: {data}')
    for i in range(callback_loop):
        try:
            response = requests.post(url, data=json.dumps(data),
                                     headers=callback_header, timeout=callback_timeout)
            logger.info('return request. status code:{} ; response info: {}'.format(
                response.status_code, response.text))
            update_flag = False
            break
        except Exception as e:
            logger.error('callback fail {}'.format(i+1))
            logger.exception(e)
    if update_flag:
        logger.error('callback fail. please check network !!!')
    else:
        logger.info('alg callback success.')
