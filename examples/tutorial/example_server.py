# -*- coding: utf-8 -*-
# @author: Yuhao Wang
# @email: wangyuhao@shanshu.ai
# @date: 2022/07/20

from example_flask_setup import main_api


def create_app():
    import flask
    app = flask.Flask(__name__)
    main_api.init_app(app)
    return app


def local_run():
    app = create_app()
    app.run(host='0.0.0.0', port=8050)


if __name__ == '__main__':
    local_run()
