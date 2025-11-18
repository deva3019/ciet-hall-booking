import flask
print("Flask version:", flask.__version__)
app = flask.Flask(__name__)
print(dir(app))
