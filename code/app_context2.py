from flask import Flask, current_app
from flask.globals import _app_ctx_stack, _request_ctx_stack
app = Flask(__name__)


if __name__ == '__main__':
    print _app_ctx_stack.top
    print _request_ctx_stack.top
    print _app_ctx_stack()
    print current_app
    ctx = app.app_context()  # push app context
    ctx.push()
    print _app_ctx_stack.top
    print _app_ctx_stack.top is ctx
    print current_app
    ctx.pop()
    print current_app