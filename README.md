
# Flask-Multiprocess-Controller

**Flask-Multiprocess-Controller** is an extension for [Flask](https://flask.palletsprojects.com/) that provides an 
easy-to-implement controller for multiprocessing tasking. It provides default functions such as task-queueing, 
health-check, status-check, manual-stop and process-safe logger. 

A common usage scenario is one has some tasks which are computational expensive and require multiple instances running 
concurrently. This controller provides a separate layer of controller by creating controlling thread for each instance.
This can greatly improve level-of-control for computational expensive tasks.


## Installation

The easiest way to install it is using ``pip`` from PyPI

```bash
pip install flask-multiprocess-controller
```

## Usage

Flask-Multiprocess-Controller provides the `MetaMPController()` class which provides default controlling method to
control the `execute()` method in the linked, child of `MetaMPTask()` class. 
Default controlling methods are as follows:
- GET: retrieve the current status of certain task in sub-process
- POST: put an execution request to the queue waiting to be executed when there is a new slot for a new sub-process
- DELETE: sending the stop signal to certain task in sub-process gently

All [Flask](https://flask.palletsprojects.com/) supported HTTP methods are supported(with necessary overrides)

One can also use `MetaMPResource()` class to adopt [Flask-RESTful](https://flask-restful.readthedocs.io) style APIs.


### Example 1: Create controller to fit in Flask Structure
```python
import logging

from flask import Flask
from flask_restful import Api
from flask_multiprocess_controller import MetaMPController, MetaMPResource, MetaMPTask

class SampleTask(MetaMPTask):
    
    def execute(self, *args, **kwargs) -> None:
        # some actions to do when receiving HTTP requests
        [...]
        # upload status to the controller
        self.upload_status('some_msg')
        [...]
        # check the stop signal, if flagged raise to the exception catcher
        self.checkpoint()
        [...]
        return

class SampleController(MetaMPController, controller_name='Sample', logger=logging.getLogger('SomeHierachy.Sample'),
                       decorator=None):
    pass

class SampleResource(MetaMPResource):
    pass

sample_api = Api()
sample_controller = SampleController(target_task=SampleTask, max_num_process=2)
sample_api.add_resource(SampleResource, '/sample', resource_class_args=(sample_controller,))
app = Flask('Sample')
sample_api.init_app(app)
app.run()

```

### Example 2: Minimal effort using build-in sub-class factory
```python
from flask import Flask
from flask_restful import Api
from flask_multiprocess_controller import TemplateFactory, MetaMPTask

class SampleTask(MetaMPTask):
    
    def execute(self, *args, **kwargs) -> None:
        # some actions to do when receiving HTTP requests
        [...]
        # upload status to the controller
        self.upload_status('some_msg')
        # check the stop signal, if flagged raise to the exception catcher
        self.checkpoint()
        [...]
        return

sample_api = Api()
sample_controller = TemplateFactory.MPController(name='Sample')(target_task=SampleTask, max_num_process=2)
sample_api.add_resource(TemplateFactory.MPResource(), '/sample', resource_class_args=(sample_controller,))
app = Flask('Sample')
sample_api.init_app(app)
app.run()

```

## License

See the [LICENSE](LICENSE.md) file for license rights and limitations (BSD-3-Clause).

## Links

- PyPI Releases: https://pypi.org/project/Flask-Multiprocess-Controller/