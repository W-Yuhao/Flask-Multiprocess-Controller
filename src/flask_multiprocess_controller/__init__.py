# -*- coding: utf-8 -*-
"""
    flask_multiprocess_controller
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Simple framework for creating Multiprocess task workers with
    an extra layer of control in Flask.

    :copyright: 2022 Yuhao Wang
    :license: BSD-3-Clause
"""

from .task import MetaMPTask
from .controller import MetaMPController
from .resource import MetaMPResource
from .utils import upload_status, set_checkpoint, AbortException
from .template import TemplateFactory
from .logger import MetaMPLoggerConfigurator

__version__ = '0.1.1'

__all__ = [
    'MetaMPTask',
    'MetaMPController',
    'MetaMPResource',
    'upload_status',
    'set_checkpoint',
    'AbortException',
    'MetaMPLoggerConfigurator',
    'TemplateFactory'
]
