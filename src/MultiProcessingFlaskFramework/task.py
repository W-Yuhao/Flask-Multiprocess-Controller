# -*- coding: utf-8 -*-
# @author: Yuhao Wang
# @date: 2022/06/20

import logging
import abc
from multiprocessing import Event, Lock, Queue
from multiprocessing.connection import Connection
from .logger import BasicLoggerConfigurator


class BasicTask(metaclass=abc.ABCMeta):
    """
    abstract meta class for task class, BasicTask instance is created inside BasicController to execute the task's
    main scripts

    execute method need to be overridden as needed
    """

    task_name: str

    def __init__(self, stop_event: Event, pipe_end: Connection, lock: Lock, queue: Queue,
                 log_configurator: type(BasicLoggerConfigurator), counter: int = 0):

        self._stop_event: Event = stop_event
        self._pipe_end: Connection = pipe_end
        self._lock: Lock = lock
        self._log_queue: Queue = queue
        self._log_configurator: type(BasicLoggerConfigurator) = log_configurator
        self.counter = counter

        # set up the worker logger when init
        self._log_configurator.worker_log_setup(self._log_queue)

    def __init_subclass__(cls, task_name: str = None, **kwargs):

        # set for default task_name
        cls.task_name = task_name
        if cls.task_name is None:
            cls.task_name = cls.__name__

    @abc.abstractmethod
    def execute(self, *args, **kwargs) -> None:
        """
        main script of a task
        for algo, it contains: Input, Data processing, Solving, Post processing, Output, Callback ...
        :param args:
        :param kwargs:
        :return:
        """
        pass

    def _abort_log(self, logger: logging.Logger) -> None:
        """
        standard log when received the stop signal
        :param logger:
        :return:
        """
        logger.critical("Task {}-{} aborted by signal.".format(self.task_name, self.counter))
