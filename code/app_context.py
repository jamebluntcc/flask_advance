from flask import Flask, current_app

app = Flask(__name__)

@app.route('/')
def index():
    return 'hello, {0}'.format(current_app.name)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=9000)

