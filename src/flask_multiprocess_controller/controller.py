# -*- coding: utf-8 -*-
# @author: Yuhao Wang
# @date: 2022/06/17

import abc
import functools
import logging
import multiprocessing
import threading
import uuid

from multiprocessing import Process, Event, Lock, Queue
from multiprocessing.connection import Connection
from queue import PriorityQueue
from typing import Dict, Tuple
from werkzeug.exceptions import MethodNotAllowed

from .logger import MetaMPLoggerConfigurator, DefaultMPLoggerConfigurator
from .utils import send_request

from .task import MetaMPTask


class MetaMPController(metaclass=abc.ABCMeta):
    """
    abstract meta class for api controller class, designed to support multiprocessing spawning from http request
    along with some controlling and communicating mechanisms
    """
    _EVENT_POS = 0
    _PIPE_POS = 1
    _LOCK_POS = 2
    _logger: logging.Logger = None
    # static bool to protect logger from been initialed twice when multiple controller exists
    _logger_init_counter: bool = False
    _name: str = 'Basic'

    def __init__(self, target_task: type(MetaMPTask), callback_url: str = None,
                 max_num_process: int = 1, max_num_queue: int = -1,
                 logger_configurator_cls: type(MetaMPLoggerConfigurator) = DefaultMPLoggerConfigurator):
        assert max_num_process > 0, "max_num_process should be greater than 0, passing {}".format(max_num_process)
        self._max_num_process = max_num_process
        # because of GIL, the following dicts are thread-safe
        # controlling thread and calculating thread may edit the following dicts concurrently
        self._process_record: Dict[int, Process] = dict()
        self._process_progress: Dict[int, int] = dict()
        self._process_primitives: Dict[int, Tuple[Event, Connection, Lock]] = dict()
        self._log_queue: Queue = Queue(-1)
        self._log_configurator = logger_configurator_cls

        # start the listening process right after creating the controller
        self._logging_thread = threading.Thread(target=self._listening_log, daemon=True, name='LogListener')
        self._logging_thread.start()

        # log the relation between controlling thread and the process being controlled
        # future cancel request or query request will need the ident of the controlling thread to link to the process
        self._control_relationship: Dict[int, int] = dict()

        # if the callback url has not be assigned, the callback is disabled
        self._callback_url: str = callback_url

        # this counter to log the times this controller is getting a post request (executing task request)
        self._call_counter = 0
        self._execute_counter = 0

        # init set the linking task to None
        self._linking_task = target_task

        # init the waiting queue and ticket system to handle waiting requests
        # using priority queue to support the shortcut functionality
        self._waiting_queue = PriorityQueue(maxsize=max_num_queue)
        self._ticket_log: Dict[str, dict] = dict()
        self._ticket_control_relationship: Dict[str, int] = dict()

        # using another thread to listen to the queue and create the control thread for each task
        self._waiting_queue_intake_event = Event()
        self._waiting_queue_listener_thread = threading.Thread(target=self._listening_queue,
                                                               daemon=True, name='QueueListener')
        self._waiting_queue_listener_thread.start()

    # noinspection PyMethodOverriding
    def __init_subclass__(cls, controller_name: str = None, logger: logging.Logger = None, decorator=None) -> None:

        # default name set to class name if not specified
        if controller_name is None:
            cls._name = cls.__name__

        # default logger set to class name on root hierarchy if not specified
        if logger is None:
            cls._logger = logging.getLogger(cls.__name__)

        # default decorator set to simple print info if not specified
        if decorator is None:
            __decorator = cls._print_request_info(cls._logger, cls._name)
        else:
            __decorator = decorator

        cls.get = __decorator(cls.get)
        cls.post = __decorator(cls.post)
        cls.head = __decorator(cls.head)
        cls.options = __decorator(cls.options)
        cls.delete = __decorator(cls.delete)
        cls.put = __decorator(cls.put)
        cls.trace = __decorator(cls.trace)
        cls.patch = __decorator(cls.patch)

    @staticmethod
    def _print_request_info(current_logger: logging.Logger, cls_name: str):
        """
        decorator for logging passing params and return value of a http request
        :param current_logger: logger assigned to the http method or the service controller
        :return:
        """
        # use the basic logger to logger if child logger has not been defined
        if current_logger is None:
            current_logger = logging.getLogger(__name__)

        def _func_define_decorator(func):
            @functools.wraps(func)
            def _decorated_func(*args, **kwargs):
                result = func(*args, **kwargs)
                current_logger.info('class {}\'s {} been called with arguments {}, return {}'.format(
                                    cls_name, func.__name__, kwargs, result))
                return result
            return _decorated_func
        return _func_define_decorator

    # By default
    # 1. GET method is to get status from a specific process-linked uuid
    # 2. POST method is to put a new request in the waiting queue to wait for execution
    # 3. DELETE method is to send TERM signal to a specific process-linked uuid

    def get(self, *args, **kwargs) -> dict:
        """
        function to run when linking resource receives a get request
        by default: to get the progress info of a process linking to the controlling thread
        :param args: args to be passed to the get method
        :param kwargs: kwargs to be passed to the get method
        :return:
        """
        task_uuid = kwargs.get('uuid', None)
        if task_uuid is not None:
            if task_uuid in self._ticket_control_relationship:
                # acquire the process object
                target_process = self._control_relationship[self._ticket_control_relationship[task_uuid]]
                # acquire Lock before reading Pipe in case the worker processes may be using it
                self._process_primitives[target_process][self._LOCK_POS].acquire()
                try:
                    progress_list = list()
                    # read all the content from the pipe
                    while self._process_primitives[target_process][self._PIPE_POS].poll():
                        progress_list.append(self._process_primitives[target_process][self._PIPE_POS].recv())
                    # update the progress dict if receive the newest progress
                    if len(progress_list) > 0:
                        self._process_progress.update({target_process: max(progress_list)})
                # release Lock after reading Pipe
                finally:
                    self._process_primitives[target_process][self._LOCK_POS].release()
                return {'msg': "Process is running with uuid {}.".format(task_uuid),
                        'progressNum': "{}".format(self._process_progress.get(target_process, 0))}
            else:
                return {'msg': "No process linked to this uuid {}.".format(task_uuid)}
        else:
            return {'msg': "Invalid request: {}".format(kwargs)}

    def post(self, *args, **kwargs) -> dict:
        """
        function to run when linking resource receives a post request
        by default: spawn a controlling thread that execute the _running method with linking_task passed
        :param args: args to be passed to the post method
        :param kwargs: kwargs to be passed to the post method
        :return:
        """
        self._call_counter += 1
        task_uuid = str(uuid.uuid4())
        # use the ticket log to log the input params
        self._ticket_log.update({task_uuid: kwargs})
        # put the request in to the waiting queue with init priority 0 if not specified
        self._waiting_queue.put_nowait((kwargs.get("priority", 0), task_uuid))

        # upon receiving new request, check the current num of processes, if able to proceed, trigger the signal
        # to queue listener thread to execute
        if len(self._process_record) < self._max_num_process:
            self._waiting_queue_intake_event.set()

        return {'msg': "Internal UUID {} for {} task put in the queue.".format(task_uuid, self._name),
                'uuid': "{}".format(task_uuid),
                'requestParams': "{}".format(kwargs),
                'taskCounter': str(self._call_counter)}

    def head(self, *args, **kwargs) -> dict:
        """
        function to run when linking resource receives a head request

        override this method if you want to use it
        :param args: args to be passed to the head method
        :param kwargs: kwargs to be passed to the head method
        :return:
        """
        raise MethodNotAllowed()

    def options(self, *args, **kwargs) -> dict:
        """
        function to run when linking resource receives a options request

        override this method if you want to use it
        :param args: args to be passed to the options method
        :param kwargs: kwargs to be passed to the options method
        :return:
        """
        raise MethodNotAllowed()

    def delete(self, *args, **kwargs) -> dict:
        """
        function to run when linking resource receives a delete request
        by default: to stop the process linking to the controlling thread safely and gracefully
        :param args: args to be passed to the delete method
        :param kwargs: kwargs to be passed to the delete method
        :return:
        """
        task_uuid = kwargs.get('uuid', None)
        if task_uuid is not None:
            if task_uuid in self._ticket_control_relationship:
                target_process = self._control_relationship[self._ticket_control_relationship[task_uuid]]
                # set the stop event to be True, let the process to exit safely
                self._process_primitives[target_process][self._EVENT_POS].set()
                # no need to do anything else as the controlling thread will monitor the process
                # and handle it itself
                return {'msg': "Stop signal sent to this uuid {}.".format(task_uuid)}
            else:
                return {'msg': "No process linked to this uuid {}.".format(task_uuid)}
        else:
            return {'msg': "Invalid request: {}".format(kwargs)}

    def put(self, *args, **kwargs) -> dict:
        """
        function to run when linking resource receives a put request

        override this method if you want to use it
        :param args: args to be passed to the put method
        :param kwargs: kwargs to be passed to the put method
        :return:
        """
        raise MethodNotAllowed()

    def trace(self, *args, **kwargs) -> dict:
        """
        function to run when linking resource receives a trace request

        override this method if you want to use it
        :param args: args to be passed to the trace method
        :param kwargs: kwargs to be passed to the trace method
        :return:
        """
        raise MethodNotAllowed()

    def patch(self, *args, **kwargs) -> dict:
        """
        function to run when linking resource receives a patch request

        override this method if you want to use it
        :param args: args to be passed to the patch method
        :param kwargs: kwargs to be passed to the patch method
        :return:
        """
        raise MethodNotAllowed()

    def _listening_log(self):
        """
        the method is to listen the log_queue and handle the log by the listening(MainProcess) logger
        :return:
        """
        if not MetaMPController._logger_init_counter:
            self._log_configurator.listener_log_setup()
            MetaMPController._logger_init_counter = True
        while True:
            try:
                record = self._log_queue.get()
                if record is None:
                    break
                logger = logging.getLogger(record.name)
                logger.handle(record)
            except IOError:
                import sys
                import traceback
                print('Problem:', file=sys.stderr)
                traceback.print_exc(file=sys.stderr)

    def _create_control_thread(self, task_uuid: str) -> None:
        """
        called by the queue listener thread to create a new control thread to execute task
        :return:
        """
        keyword_arguments = self._ticket_log[task_uuid]
        post_thread = threading.Thread(target=self._running, args=(task_uuid, self._linking_task,),
                                       kwargs=keyword_arguments, daemon=True, name='POST_THREAD')
        post_thread.start()
        self._ticket_control_relationship.update({task_uuid: post_thread.ident})

    def _listening_queue(self):
        """
        listen the queue and create control thread when signal is sent
        :return:
        """
        while True:
            # only on two occasions will this event be set
            # 1. when receiving a new request
            # 2. upon completion of one task
            self._waiting_queue_intake_event.wait()
            self._waiting_queue_intake_event.clear()
            # position 0 is the priority, position 1 is the task uuid
            task_uuid = self._waiting_queue.get(block=True)[1]
            self._create_control_thread(task_uuid)

            if self._callback_url is not None:
                callback_msg = {"msg": "Task with internal uuid {} begin to process".format(task_uuid),
                                "uuid": task_uuid}
                send_request(self._callback_url, callback_msg)

    def _running(self, task_uuid: str, target_task: type(MetaMPTask), *args, **kwargs) -> None:
        """
        this method is called by the controlling thread to create, run and control the calculating process to execute
        target_function
        :param task_uuid: the task uuid linked to the task
        :param target_task: the task that separate process will execute in the form of the task object
        :return:
        """

        assert isinstance(target_task, type), \
            "Invalid input, target_task must be a class, instead of {}".format(type(target_task))

        assert issubclass(target_task, MetaMPTask), \
            "Invalid class {}, target_task must inherit from BasicTask".format(target_task)

        # creating the primitive the process will need to use
        # Event is to send Stop signal to the process
        # Pipe is to get progress info of the process (one-way: process -> controlling thread)
        # Lock is to guard Pipe from race condition
        new_event = multiprocessing.Event()
        new_event.clear()
        parent_connection, child_connection = multiprocessing.Pipe(duplex=False)
        new_lock = multiprocessing.Lock()

        # maintaining the counter in the controller instead of the task for it will get instantiated every time
        target_task.counter += 1
        # set running process to daemon in case that the running process may be orphaned
        # after the main process exit exceptionally
        task_obj = target_task(*(new_event, child_connection, new_lock, self._log_queue, target_task.counter,
                                 self._log_configurator) + args)
        new_process = multiprocessing.Process(target=task_obj.execute,
                                              name=str(task_obj.task_name) + '-' + str(target_task.counter),
                                              args=args, kwargs=kwargs, daemon=True)
        # create another process and run
        new_process.start()
        # after process ID(pid) has been generated, log the thread, process and its primitives info
        self._process_record.update({new_process.pid: new_process})
        self._process_primitives.update({new_process.pid: (new_event, parent_connection, new_lock)})
        self._control_relationship.update({threading.current_thread().ident: new_process.pid})

        # hold until the controlled process exit either normally or forcefully
        new_process.join()

        # clean procedure for Pipe, Event and Lock
        while parent_connection.poll():
            parent_connection.recv()
        parent_connection.close()
        self._process_primitives.pop(new_process.pid)

        # clean procedure for all the records
        self._process_record.pop(new_process.pid)
        self._process_progress.pop(new_process.pid, None)
        self._control_relationship.pop(threading.current_thread().ident)
        self._ticket_log.pop(task_uuid)
        self._ticket_control_relationship.pop(task_uuid)

        # after a task is complete, there always a room for a new task to be executed
        self._waiting_queue_intake_event.set()

        if self._callback_url is not None:
            callback_msg = {"msg": "Task with internal uuid {} ended".format(task_uuid),
                            "uuid": task_uuid}
            send_request(self._callback_url, callback_msg)
