import random

from flask import Flask, render_template
from werkzeug.local import LocalStack, LocalProxy

from ext import db
from users import User

app = Flask(__name__)
app.config.from_object('config')
db.init_app(app)

_user_stack = LocalStack()


def get_current_user():
    top = _user_stack.top
    if top is None:
        raise RuntimeError()
    return top


current_user = LocalProxy(get_current_user)


@app.before_first_request
def setup():
    db.drop_all()
    db.create_all()
    fake_users = [
        User('chencheng', 'chen@cheng.com'),
        User('lxgui', 'lxgui@163.com')
    ]
    db.session.add_all(fake_users)
    db.session.commit()


@app.before_request
def befor_request():
    users = User.query.all()
    user = random.choice(users)
    _user_stack.push(user)


@app.teardown_appcontext
def teardown(exc=None):
    if exc is None:
        db.session.commit()
    else:
        db.session.rollback()
    db.session.remove()
    _user_stack.pop()


@app.context_processor
def template_extras():
    return {'enumerate': enumerate, 'current_user': current_user}


@app.errorhandler(404)
def page_not_found(error):
    return 'this page not exist', 404


@app.template_filter('capitalize')
def reverse_filter(s):
    return s.capitalize()


@app.route('/users')
def user_view():
    users = User.query.all()
    return render_template('user.html', users=users)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000)


