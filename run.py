from flask import Flask
from app.routes import router
from app.utils.socketio import socketio

def create_app():
    app = Flask(__name__, static_folder="app/static")
    app.register_blueprint(router)
    socketio.init_app(app)
    return app

if __name__ == '__main__':
    app = create_app()
    socketio.run(app, debug=True)