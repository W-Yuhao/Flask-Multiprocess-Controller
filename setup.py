"""
Flask-Multiprocess-Controller
=============================

**Flask-Multiprocess-Controller** is an extension for `Flask`_ that provides an
easy-to-implement controller for multiprocessing tasking. It provides default functions such as task-queueing,
health-check, status-check, manual-stop and process-safe logger.

A common usage scenario is one has some tasks which are computational expensive and require multiple instances running
concurrently. This controller provides a separate layer of controller by creating controlling thread for each instance.
This can greatly improve level-of-control for computational expensive tasks.


Features
--------

Flask-Multiprocess-Controller provides the `MetaMPController()` class which provides default controlling method to
control the `execute()` method in the linked, child of `MetaMPTask()` class.
Default controlling methods are as follows:
- GET: retrieve the current status of certain task in sub-process
- POST: put an execution request to the queue waiting to be executed when there is a new slot for a new sub-process
- DELETE: sending the stop signal to certain task in sub-process gently

All `Flask`_ supported HTTP methods are supported(with necessary overrides)

One can also use `MetaMPResource()` class to adopt `Flask-RESTful`_ style APIs.


Example: Build a minimal Controller-Task structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the following example, we will use the built-in ``TemplateMPController``, and ``TemplateMPResource`` to build the
structure of controller-task framework. One may need to override some methods in ``MetaMPController``
for more functionality.

.. code:: python

    import logging
    from flask import Flask
    from flask_restful import Api
    from flask_multiprocess_controller import TemplateFactory, MetaMPTask

    class SampleTask(MetaMPTask):

        def execute(self) -> None:
            task_logger = logging.getLogger(str(os.getpid()))
            counter = 0
            while counter < 100:
                counter += 1
                task_logger.debug("doing some simple task, progress {}%.".format(counter))
                time.sleep(0.5)
                self.upload_status(counter)
                self.checkpoint()

    sample_api = Api()
    sample_controller = TemplateFactory.MPController(name='Sample')(target_task=SampleTask, max_num_process=2)
    sample_api.add_resource(TemplateFactory.MPResource(), '/sample', resource_class_args=(sample_controller,))

    app = Flask('Sample')
    sample_api.init_app(app)
    app.run()


Installation
------------
The easiest way to install it is using ``pip`` from PyPI

.. code:: bash

    pip install flask-multiprocess-controller


License
-------

See the `LICENSE`_ file for license rights and limitations (BSD-3-Clause).


.. _Flask: https://flask.palletsprojects.com/
.. _Flask-RESTful: https://flask-restful.readthedocs.io
.. _LICENSE: https://github.com/W-Yuhao/Flask-Multiprocess-Controller/blob/master/LICENSE.md

"""
import re
import ast
from setuptools import setup, find_packages

_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('src/flask_multiprocess_controller/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

setup(
    name='Flask-Multiprocess-Controller',
    version=version,
    url='https://github.com/W-Yuhao/Flask-Multiprocess-Controller',
    license='BSD-3-Clause',
    author='Yuhao Wang',
    author_email='hotaro0724@gmail.com',
    description='Flask extension that provides an easy-to-implement controller for multiprocessing tasking. '
                 'It provides default functions such as task-queueing, health-check, status-check, '
                 'manual-stop and process-safe logger.',
    long_description=__doc__,
    long_description_content_type='text/x-rst',
    maintainer="Yuhao Wang",
    maintainer_email="hotaro0724@gmail.com",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    python_requires=">=3.7",
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Flask~=1.1',
        'requests~=2.25',
        'Werkzeug~=1.0',
        'flask_restful~=0.3'
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ])
