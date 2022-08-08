# -*- coding: utf-8 -*-
"""
    flask_multiprocess_controller.template
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This module implements templates that can generate MPController and MPResource class definition automatically.

    TemplateFactory may be readily useful when there is no need to redeclare and override MPController and MPResource.

    :copyright: 2022 Yuhao Wang
    :license: BSD-3-Clause
"""

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
