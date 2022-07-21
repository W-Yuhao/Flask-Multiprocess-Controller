# -*- coding: utf-8 -*-
# @author: Yuhao Wang
# @date: 2022/07/19

import logging
import abc

from logging import StreamHandler
from logging.handlers import TimedRotatingFileHandler
from multiprocessing import Queue


class MetaMPLoggerConfigurator(metaclass=abc.ABCMeta):

    @staticmethod
    @abc.abstractmethod
    def listener_log_setup():
        """
        set up the listening log format and handlers
        :return:
        """
        pass

    @staticmethod
    def worker_log_setup(queue: Queue):
        """
        worker logger can't have any handler other than QueueHandler
        its sole purpose is to send log record through the queue

        worker logger's format contains only message for the listening logger with do the formatting

        worker logger mustn't use root as name, since the root logger is defined as listening logger with
        formatters and other handles

        ONLY OVERRIDE THIS METHOD IF YOU KNOW WHAT YOU'RE DOING

        :param queue: log queue passed to the listening thread
        :return:
        """
        logger = logging.getLogger('MAIN_WORKER')
        queue_handler = logging.handlers.QueueHandler(queue)
        queue_handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(queue_handler)
        # pass everything to the listening logger
        logger.setLevel(logging.DEBUG)


class DefaultMPLoggerConfigurator(MetaMPLoggerConfigurator):
    """
    Default multiprocessing logger, only contains a single stream handler
    """

    @staticmethod
    def listener_log_setup():
        """
        set up the listening log format and handlers
        :return:
        """
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        log_formatter = logging.Formatter(
            '[%(threadName)-8s][%(processName)-8s][%(levelname)-8s][%(asctime)s][%(name)-75s] %(message)s')

        stream_handler = StreamHandler()
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(log_formatter)
        logger.addHandler(stream_handler)
