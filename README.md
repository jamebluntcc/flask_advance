## flask advance

1 flask 中的上下文
- 程序上下文
 -  current app
 -  g

- 请求上下文 
 - request
 - session
创建应用上下文
```python
from flask import Flask, current_app

app = Flask(__name__)
with app.app_context():
	print current_app.name
```

从一个 Flask app 读入配置并启动开始，就进入了 `App Context`，其中我们可以访问到配置文件，打开资源文件，
通过路由规则反向构造 URL 等。
```python
from flask import Flask, current_app
app = Flask(__name__)

@app.route('/')
def index():
	return 'Hello {0}'.format(current_app.name)
```
如上程序可以很自然的读出
创建请求上下文
```python
from flask import request
from werkzeug.test import EnvironBuilder
ctx = app.request_context(EnvironBuilder('/', 'http://localhost/').get_environ())
ctx.push()
try:
	print request.url
finally:
	ctx.pop()
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
thread.join()
print log  # [13]
print mydata.number  # 12  # 主线程没有改变
```

因此只有有`Thread Local`对象，就能让同一个对象在多个线程下做到状态的隔离。在 Flask 中是基于 `WerkZeug` 的
`Local Stack` 实现的，两种上下文对象定义在 `flask.ctx`中，`ctx.push`会将当前的上下文对象压栈到`flask._request_ctx_stack` 中，这个对象也是个`Thread Local` 对象，上下文压入栈后，再次请求的时候都是通过
`_request_ctx_stack.top`  在栈顶取得，所取的永远都是属于自己的线程对象，这样不同线程之间的上下文就都做到了隔离。请求结束后，`ctx.pop()`弹出上下文对象回收内存。


2 对于 `url_for`  最常见的使用有两个：
 - 作为常规链接使用 `url_for('view func name')` 接受一个字符串，其值为视图函数的名字
 - 作为静态文件的特殊路由 `url_for('static', filename='')` 可以作为内部文件与用户进行互通
 
 
3 web 表单
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
