# -*- coding: utf-8 -*-
# @author: Yuhao Wang
# @date: 2022/06/20

import logging
import abc
from functools import wraps
from multiprocessing import Event, Lock, Queue
from multiprocessing.connection import Connection
from .logger import MetaMPLoggerConfigurator
from .utils import AbortException


class MetaMPTask(metaclass=abc.ABCMeta):
    """
    abstract meta class for task class, BasicTask instance is created inside BasicController to execute the task's
    main scripts

    execute method need to be overridden as needed
    """

    # the counter is exposed as static for the controller to retrieve the counter info
    counter: int = 0
    task_name: str
    logger: logging.Logger

    def __init__(self, stop_event: Event, pipe_end: Connection, lock: Lock, queue: Queue, counter: int,
                 log_configurator: type(MetaMPLoggerConfigurator)):

        self._stop_event: Event = stop_event
        self._pipe_end: Connection = pipe_end
        self._lock: Lock = lock
        self._log_queue: Queue = queue
        self._log_configurator: type(MetaMPLoggerConfigurator) = log_configurator
        self.counter: int = counter

        # set up the worker logger when init
        self._log_configurator.worker_log_setup(self._log_queue)

    def __init_subclass__(cls, task_name: str = None, logger: logging.Logger = None, **kwargs):
        # set for default task_name
        if task_name is None:
            cls.task_name = cls.__name__

        # default logger set to class name on root hierarchy if not specified
        if logger is None:
            cls.logger = logging.getLogger(cls.__name__)

        # catch AbortException when when receiving STOP signal, necessary for gently stop
        cls.execute = cls._exception_catcher(cls.execute)

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

    def upload_status(self, msg) -> None:
        """
        safely send msg using Pipe between processes by Lock
        :param msg: message to send
        :return:
        """
        self._lock.acquire()
        try:
            self._pipe_end.send(msg)
        finally:
            self._lock.release()

    def set_checkpoint(self) -> None:
        """
        check the stop signal, if met raise AbortException and exit gently
        :return:
        """
        if self._stop_event.is_set():
            raise AbortException("Task {}-{} aborted by signal.".format(self.task_name, self.counter))

    @classmethod
    def _exception_catcher(cls, execute):
        @wraps(execute)
        def with_exception_catcher_execute(*args, **kwargs):
            try:
                execute(*args, **kwargs)
            except AbortException as ae:
                cls.logger.info(ae)
            except Exception as e:
                cls.logger.critical(e)
        return with_exception_catcher_execute
