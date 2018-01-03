## flask 进阶

### flask context

flask 的一个比较经典的设计是 `App context` 与 `Request context`。

1 flask 中的上下文
- 程序上下文
	 -  current app
	 -  g

- 请求上下文 
	 - request
	 - session

从一个 Flask app 读入配置并启动开始，就进入了 `App Context`，其中我们可以访问到配置文件，打开资源文件，
通过路由规则反向构造 URL 等。

```python
from flask import Flask, current_app
app = Flask(__name__)

@app.route('/')
def index():
	return 'Hello {0}'.format(current_app.name)
```

如上程序可以很自然的读出 current_app.name，`current_app` 是一个本地代理，它的类型是 `werkzeug.local.LocalProxy` 它所代理的即是我们的 app 对象，也就是 `current_app == LocalProxy(app)`。使用 `current_app` 是因为它也是一个 `ThreadLocal` 变量，对它的改动不会影响到其它的线程。可以使用 `current_app._get_current_object()` 方法来取得 app 对象。

在离线脚本里也可以显式的建立一个`App Context`：

```python
from flask import Flask, current_app

app = Flask(__name__)
with app.app_context():
	print current_app.name
```

对于 Flask Web 来说每一个请求都是一个独立的线程，因为每一个请求都不是独立的话，想象下同时多个用户在发送请求的时候请求必须是独立，要不然会出现数据的冲突。请求之间的信息要完全隔离，避免冲突，这里就必须需要使用到 `Thread Local`。

在 python 中实现最简单的 `Thread Local` 方法如下：
```python
import threading
mydata = threading.local() # 创建 Thread Local 对象
mydata.number = 12
log = []
def f():
	mydata.number = 13
	log.append(mydata.number) # 在这线程里已经修改了数据

thread = threading.Thread(target=f)
thread.start()
print log  # [13]
print mydata.number  # 12  # 主线程没有改变
```

因此只有`Thread Local`对象，就能让同一个对象在多个线程下做到状态的隔离。在 Flask 中 基于`werkzeug` 实现了自己的本地线程，同时还实现了两种数据结构：
- LocalStack: 基于 `werkzeug.local.Local` 实现的栈结构，可以将对象推入，弹出，也可以快速拿到栈顶对象。
-  LocalProxy: 标准的代理模式，构造此结构的时候接受一个可以调用的对象，一般是函数，这个函数在被调用后返回一个本身就是`Thread Local`对象。它是通过 `LocalStack` 实例化的栈顶对象。对于这个 `LocalProxy` 的处理都会转发到这个栈顶对象上。

在 flask 中，`App Context` 表示了应用级别的上下文，比如说配置文件中的数据库连接信。`Request Context` 代表的是请求级别的上下文。如当前访问的 URL。

这两种上下文对象都定义在 `flask.ctx` 中，它们的用法是推入 `flask.globals` 中创建的 `_app_ctx_stack`和`_request_ctx_stack`这两个实例化的 `Local Stack`对象。

```python
from flask import Flask, current_app
from flask.globals import _app_ctx_stack, _request_ctx_stack
app = Flask(__name__)

if __name__ == '__main__':
	print _app_ctx_stack.top
	print _request_ctx_stack.top
	print _app_ctx_stack()
	print current_app
	# 推入 app context
	ctx = app.app_context()
	ctx.push()
	print _app_ctx_stack.top
	print _app_ctx_stack.top is ctx
	print current_app
	ctx.pop()
	print current_app
```

需要注意的是当使用 `app = Flask(__name__)` 构造出一个 `Flask App` 时，并不会被自动推入 Stack，所以此时的 Local Stack 的栈顶是空的， `current_app` 也是 unbound 状态。

所以在离线脚本中连接数据库的时候，当我们使用 `Flask-SQLalchemy` 写成的 Model 上调用 `User.query.get(user_id)` 就会立即出现 `RuntimeError`。因为此时的 `App Context` 还没有被推入栈中，而 Flask-SQLalchemy 需要做数据库连接的时候取访问 `current_app.config` current_app 指向的却是 `_app_ctx_stack` 为空的栈顶。所以一般要先将 App 的 APP Context 推入栈中，栈顶不为空后 `current_app` 这个 LocalProxy 对象就很自然的取得 config 属性转发到当前 APP 上。 

但是需要注意的一点是在我们应用启动后并不需要显式的推入 APP context，原因是在于在请求上下文发生后，如果没有检查到 APP context 就会隐式的推入一个应用上下文。
```python
from flask import request, Flask

app = Flask(__name__)
@app.route('/people/')
def people():
	name = request.args.get('name')
```

这里当用户访问 /people/ 的时候，flask 会去找一个叫做` _request_ctx_stack` 的栈顶对象，它就是 `LocalProxy` 的实例。

```python
from functools import partial
from werkzeug.local import LocalProxy

def _lookup_req_object(name):
	top = _request_ctx_stack.top
	if top is None:
		raise RuntimeError('working outside of request context')
	return getattr(top, name)

request = LocalProxy(partial(_lookup_req_object, 'request'))

```
在 flask  中有这样的几个 hook 装饰器：
- before_first_request：在处理第一次请求之前执行。
- before_request：在每次请求前执行。
- teardown_appcontext：不管有无异常，注册函数都会在每次请求后执行。
- context_processor：上下文处理的装饰器，返回的字典中的键可以在上下文中使用。
- errorhandle：errorhandle 接受状态码，可以自定义返回这种状态码的响应处理方法。
- template_filter：在使用`jinja2`模板的时候可以方便的注册过滤器。

接下来在 code 中的 [app_with_local_proxy.py](https://github.com/jamebluntcc/flask_advance/) 可以看到演示代码，如何使用`LocalProxy` 代替 `flask.g`。其中 get_current_user 返回`LocalStack`的栈对象，然后使用`LocalProxy`进行代理，结果返回一个应用上下文对象，在应用上下文以及请求上下文中被作为全局变量使用。


### flask url

对于 `url_for`  最常见的使用有两个：
 - 作为常规链接使用 `url_for('view func name')` 接受一个字符串，其值为视图函数的名字
 - 作为静态文件的特殊路由 `url_for('static', filename='')` 可以作为内部文件与用户进行互通
 

### flask form

web 表单是作为前端用户最常用的输入，通过`request.form`对象传递到后台。在 flask 中有 `flask-wtf` 与 `wtforms`协同实现 web 表单的生成和验证，一般的 flask web application 中会将 forms 作为一个独立的模块进行处理。进阶的 form 会对 validate 方法进行继承扩展，详细请参考[flask auth system](https://github.com/jamebluntcc/flask_auth_system) 里面的 form 设计。值得注意的是 `flask-wtf` 中的表单都实现了`CSRF`保护，在 config 文件中增加一个`SECRET_KEY`的值便可实现此功能。关于表单在 HTML 上的渲染也可以参考上面的 flask-auth-system 项目。
这里再多提一点就是关于 `flash` 消息的使用，当用户在 web 表单中进行了相应的输入，页面需要作出相应的反馈的时间。`flash` 就变得很有用，在 HTML 中 flask 开放了 `get_flashed_messages()` 给模板，用于获取并渲染信息。
HTML 的渲染模板如下：
```
{% for message in get_flashed_messages() %}
<div class="alert alert-warning">
	<button type="button" class="close" data-dismiss="alert">&times;</button>
		{{ message }}
</div>
{% endfor %}
```
