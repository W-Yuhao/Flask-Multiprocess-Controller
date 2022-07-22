# -*- coding: utf-8 -*-
# @author: Yuhao Wang
# @date: 2022/06/17

import inspect
import json

from flask import request
from flask_restful import Resource

from .controller import MetaMPController


class MetaMPResource(Resource):
    """
    overridden resource class to take BasicController as its controller, and execute controller's method when get
    http request from WSGI server
    """

    def __init__(self, controller: MetaMPController):
        super(MetaMPResource, self).__init__()
        self._controller = controller

    # all supported http methods are predefined to linked to the _controller object

    def get(self):
        return self.__return_controller_func()

    def post(self):
        return self.__return_controller_func()

    def head(self):
        return self.__return_controller_func()

    def options(self):
        return self.__return_controller_func()

    def delete(self):
        return self.__return_controller_func()

    def put(self):
        return self.__return_controller_func()

    def trace(self):
        return self.__return_controller_func()

    def patch(self):
        return self.__return_controller_func()

    @staticmethod
    def _get_request_dict(request_obj: request) -> dict:
        """
        transform http request input to dict object

        :param request_obj:
        :return:
        """
        if len(request_obj.data):
            return json.loads(request_obj.data)
        else:
            return dict()

    def __return_controller_func(self) -> any:
        """
        use the Resource class to run the _controller's http request method in flask-restful style

        :return: any object that returned from _controller's http request method
        """
        func = getattr(self._controller, inspect.currentframe().f_back.f_code.co_name)
        return func(**self._get_request_dict(request))
