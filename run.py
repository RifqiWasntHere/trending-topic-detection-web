from flask import Flask
from app.routes import router  # import the blueprint

def create_app():
    app = Flask(__name__, static_folder='app/static')
    app.register_blueprint(router)  # register blueprint
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)