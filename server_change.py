from flask import Flask

app = Flask(__name__)
app.config['SERVER_NAME'] = 'localhost:5000'

if __name__ == '__main__':
    app.run()
