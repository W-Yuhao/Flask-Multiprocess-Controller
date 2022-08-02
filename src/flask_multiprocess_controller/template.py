# -*- coding: utf-8 -*-
# @author: Yuhao Wang
# @date: 2022/07/21

import uuid

from .resource import MetaMPResource
from .controller import MetaMPController


class TemplateFactory(object):
    """
    Factory to create a child class type from MetaMPResource or MetaMPController with default functionality
    """

    @staticmethod
    def MPController(name: str = None) -> type:
        """
        create a child class type from MetaMPController
        :param name: if not defined, will automatically create a uuid4 style id as name
        :return:
        """
        if not name:
            name = "Controller-" + str(uuid.uuid4())
        return type(name, (MetaMPController,), dict())

    @staticmethod
    def MPResource(name: str = None) -> type:
        """
        create a child class type from MetaMPResource
        :param name: if not defined, will automatically create a uuid4 style id as name
        :return:
        """
        if not name:
            name = "Resource-" + str(uuid.uuid4())
        return type(name, (MetaMPResource,), dict())
