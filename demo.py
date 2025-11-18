from flask import Flask

app = Flask(__name__)

@app.before_first_request
def test_func():
    print("SUCCESS!")

if __name__ == '__main__':
    app.run()
