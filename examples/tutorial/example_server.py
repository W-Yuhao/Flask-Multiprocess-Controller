# -*- coding: utf-8 -*-
"""
    The example implementation of server setup.

    Provides both gunicorn and python ways to boot the server.

    :copyright: 2022 Yuhao Wang
    :license: BSD-3-Clause
"""

# one must protect all the create_app and run_app method from the spawning process
# don't use the __init__ file to create app
# for the spawning process will create a flask app for itself of no use


def create_app():
    """
    gunicorn way to start the server
    command: gunicorn 'example_server:create_app()'
    :return:
    """
    import flask
    from example_main_api import main_api
    from example_local_callback_api import local_callback_api
    app = flask.Flask(__name__)
    main_api.init_app(app)
    local_callback_api.init_app(app)
    return app


def local_run():
    """
    python way to start the server
    command: python example_server.py

    DO NOT USE IT IN A PRODUCTION ENVIRONMENT
    :return:
    """
    app = create_app()
    app.run(host='0.0.0.0', port=8050)


if __name__ == '__main__':
    local_run()
