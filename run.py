from flaskApp import app
from dotenv import load_dotenv

load_dotenv() #把API_KEY存在环境变量里，可以import os 来调用
if __name__ == "__main__":
    app.run(debug=True, port=8080)
