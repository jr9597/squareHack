from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return 'This is our humble homepage'





if __name__ == "__main__":
    app.run(debug=True)