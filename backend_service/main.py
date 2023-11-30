"""
source ~/envs/envflaskrest/Scripts/activate
python main.py

celery -A main worker --loglevel INFO
celery -A main beat --loglevel INFO
"""
import logging
import uuid
from functools import wraps

from flask_restful import Api
from flask_restful import Resource, abort

from flask import request
from werkzeug.exceptions import HTTPException
from webargs import fields
from webargs.flaskparser import parser, use_args, use_kwargs
from marshmallow import Schema
from marshmallow.utils import missing

from config import create_app
from tasks import send_register_email

logging_format ='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(filename='server.log', encoding='utf-8', format=logging_format, level=logging.INFO)


flask_app = create_app()
celery_app = flask_app.extensions["celery"]
api = Api(flask_app)


class APIException(HTTPException):
    code = 400


class WebhookAuthenticator:
    def authenticate(self, request):
        auth = self.get_authorization_header(request)
        if not auth:
            msg = "Invalid token header. No credentials provided."
            raise APIException(msg)
        
        try:
            token = auth.decode()
        except UnicodeError:
            msg = 'Invalid token header. Token string should not contain invalid characters.'
            raise APIException(msg)
        
        if token != 'ashish':
            msg = "Invalid token."
            raise APIException(msg)
        
        return token

    def get_authorization_header(self, request):
        """
        Return request's 'Authorization:' header, as a bytestring.

        Hide some test client ickyness where the header can be unicode.
        """
        headers = parser.load_headers(request, schema=Schema.from_dict({})())
        auth = headers.get('X-Webhook-Token', b'')
        if isinstance(auth, str):
            # Work around django test client oddness
            auth = auth.encode('iso-8859-1')
        return auth


def handle_authentication(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        authenticator = WebhookAuthenticator()

        try:
            authorized = authenticator.authenticate(request)  # custom account lookup function
        except APIException as exc:
            print(f"APIException: {exc}")
            authorized = None

        if not authorized:
            print("unauthorized request. No further processing.")
            abort(401)

        return func(*args, **kwargs)
    return wrapper


def handle_logging(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logging.info("%s - %s - %s" % (request.method, request.path, request.data))

        return func(*args, **kwargs)
    return wrapper


class HelloWorld(Resource):
    method_decorators = [handle_logging]

    def get(self):
        return {'hello': 'world'}


class UserRegister(Resource):
    method_decorators = [handle_logging]

    def post(self):
        params = parser.load_json(request, schema=Schema.from_dict({}))
        username = params.get("username")
        if not username:
            msg = "username missing."
            return {"detail": msg}

        response = dict(
            first_name = str(params.get("first_name")),
            username = str(username),
            email = str(params.get("email")),
            password = str(params.get("password")),
            token = uuid.uuid1().hex,
        )
        result = send_register_email.delay(username)
        response.update({
            "result_id": str(result),
            "detail": "register success."         
        })

        return response


class ApiWebhook(Resource):
    # method_decorators = [handle_authentication]
    method_decorators = {'post': [handle_logging, handle_authentication]}

    def post(self):
        params = parser.load_json(request, schema=Schema.from_dict({}))
        headers = parser.load_headers(request, schema=Schema.from_dict({})())
        headers_dct = {k:v for k,v in headers.items() if headers}

        return {"params": params, "headers": headers_dct, "X-Lyft-Token": headers_dct.get('X-Webhook-Token')}


api.add_resource(HelloWorld, '/')
api.add_resource(UserRegister, '/register')
api.add_resource(ApiWebhook, '/webhook')


if __name__ == '__main__':
    flask_app.run(debug=True, host="0.0.0.0", port=5000)