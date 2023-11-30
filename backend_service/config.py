"""
flask-restful==0.3.9
webargs==8.3.0
requests==2.29.0
celery==5.3.6
redis
pypiwin32
"""
import os
from flask import Flask
from celery import Celery, Task
from pathlib import Path

DEBUG = os.environ.get('DEBUG', None)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
print("DEBUG: %s BASE_DIR: %s" % (DEBUG, BASE_DIR))

def get_celery_config():
    REDIS_HOST = os.environ.get('REDIS_HOST', None)
    print("DEBUG: %s REDIS_HOST: %s" % (DEBUG, REDIS_HOST))

    if REDIS_HOST:
        return dict(
            broker_url="redis://{}:6379/0".format(REDIS_HOST),
            result_backend="redis://{}:6379/0".format(REDIS_HOST),
        )
    else:
        # paths for file backend, create folders
        _root = Path(__file__).parent.resolve().joinpath('logs')
        _backend_folder = _root.joinpath('results')
        _backend_folder.mkdir(exist_ok=True, parents=True)
        _folders = {
            'data_folder_in': _root.joinpath('in'),
            'data_folder_out': _root.joinpath('in'),  # has to be the same as 'data_folder_in'
            'processed_folder': _root.joinpath('processed')
        }
        for fn in _folders.values():
            fn.mkdir(exist_ok=True)
        return dict(
            broker_url="filesystem://",
            broker_transport_options={k: str(f) for k, f in _folders.items()},
            task_ignore_result=True,
        )


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(CELERY_CONFIG=get_celery_config(),)
    app.config.from_prefixed_env()
    celery_init_app(app)
    return app


def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name)
    celery_app.config_from_object(app.config["CELERY_CONFIG"], namespace='CELERY')
    celery_app.Task = FlaskTask
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app
