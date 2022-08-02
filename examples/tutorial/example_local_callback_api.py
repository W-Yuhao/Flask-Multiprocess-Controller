# -*- coding: utf-8 -*-
# @author: Yuhao Wang
# @date: 2022/08/02

import os
import logging
from flask_restful import Api
from src.flask_multiprocess_controller import *


# Here also shows that if multiprocess controller isn't needed (e.g. performing simple tasks), one can override the
# MetaMPController class's http method as desired
class LocalCallbackController(MetaMPController):

    def post(self, **kwarg):
        logger = logging.getLogger("LocalCallback-" + str(os.getpid()))
        logger.info(kwarg)
        return kwarg


local_callback_api = Api()

local_callback_controller = LocalCallbackController(target_task=None, max_num_process=1)

local_callback_api.add_resource(TemplateFactory.MPResource(), '/local_callback',
                                resource_class_args=(local_callback_controller,))
