# -*- coding: utf-8 -*-
"""
    The example implementation of Controller-Task-Resource structure of a time-consuming task
    when using flask_multiprocess_controller package.

    :copyright: 2022 Yuhao Wang
    :license: BSD-3-Clause
"""

import os
import logging
import time
from flask_restful import Api
from src.flask_multiprocess_controller import *


class MainTask(MetaMPTask):

    def execute(self, *args, **kwargs) -> None:
        task_logger = logging.getLogger("Main-" + str(os.getpid()))

        task_logger.info("MAIN_TASK starts executing by process {}".format(os.getpid()))
        task_logger.info("Getting param: {}".format(kwargs))

        # doing some simple task
        counter = 0
        while counter < 20:
            counter += 1
            task_logger.debug("doing some simple task, progress {}%.".format(counter * 5))
            time.sleep(0.5)
            # upload status to the controller
            self.upload_status(counter)
            # check the stop signal, if flagged raise AbortException to the exception catcher
            self.set_checkpoint()

        task_logger.info("Execution Finished!")


main_api = Api()
# this is the place to config the max num of processes you'd like to use in this specific controller

# if there is no need to override any functionality in MetaMPController, one can use the TemplateFactory to fastly
# create MPController class for easier use
main_controller = TemplateFactory.MPController(name='Main')(
    target_task=MainTask, max_num_process=2, callback_url='http://127.0.0.1:8050/local_callback')

# must pass the controller object to the resource object
# when received a http request, a new resource instance will be created, so it's not possible to store info in
# resource object

# if there is no need to override any functionality in MetaMPResource, one can use the TemplateFactory to fastly
# create MPResource class for easier use
main_api.add_resource(TemplateFactory.MPResource(name='Main'), '/main', resource_class_args=(main_controller,))

