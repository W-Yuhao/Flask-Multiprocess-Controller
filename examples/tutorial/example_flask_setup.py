# -*- coding: utf-8 -*-
# @author: Yuhao Wang
# @date: 2022/07/20

import os
import logging
import time
from flask_restful import Api
from src.flask_multiprocess_controller import *


class MainTask(MetaMPTask):

    def execute(self, *args, **kwargs) -> None:
        task_logger = logging.getLogger(str(os.getpid()))

        task_logger.info("MAIN_TASK starts executing by process {}".format(os.getpid()))
        task_logger.info("Getting param: {}".format(kwargs))

        # doing some simple task
        counter = 0
        while counter < 20:
            counter += 1
            task_logger.debug("doing some simple task, progress {}%.".format(counter * 5))
            time.sleep(0.5)
            self.upload_status(counter)
            self.checkpoint()

        task_logger.info("Execution Finished!")


main_api = Api()
# this is the place to config the max num of processes you'd like to use in this specific controller
main_controller = TemplateMPController(target_task=MainTask, max_num_process=2)

# must pass the controller object to the resource object
# when received a http request, a new resource instance will be created, so it's not possible to store info in
# resource object
main_api.add_resource(TemplateMPResource, '/main', resource_class_args=(main_controller,))
