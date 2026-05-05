import os
from flask import Flask
from flask import render_template
from flask import request
from flask import session
from flask import redirect
from flask import url_for
from flask import jsonify

from flask_socketio import SocketIO, send, emit

from . import db_handler
from . import util


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='7cca336dced46400b461a991f88b3609d57f6b39312ac3c96a5253d69d22804f',
        DATABASE=os.path.join(app.instance_path, 'schema.sqlite'),
    )

    with app.app_context():
        db_handler.init_db()
    app.teardown_appcontext(db_handler.close_db)

    socketio = SocketIO(app)
    users = {}
    usercount = 0

    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    @app.route("/")
    def main():
        if 'username' not in session:
            return redirect(url_for('login_page'))
        
        return render_template('chat.html', username=session['username'])

    @app.route("/login", methods=['POST', 'GET'])
    def login_page():
        if 'username' in session:
            session.pop('username', None)
        error = ''
        username = ''
        password = ''
        if request.method == 'POST':
            login_err = db_handler.validate_login(request.form['username'], request.form['password'])
            if login_err == None:
                session['username'] = request.form['username']
                return redirect(url_for('main'))
            else:
                error = login_err
                username = request.form['username']
                password = request.form['password']
        return render_template('login.html', username=username, password=password, err=error)

    @app.route("/register", methods=['POST', 'GET'])
    def register_page():
        if 'username' in session:
            session.pop('username', None)
        error = ''
        username = ''
        email = ''
        password = ''
        password_confirm = ''
        if request.method == 'POST':
            e = db_handler.add_login(request.form['username'], request.form['email'], request.form['password'], request.form['password_confirm'])
            if(e == None):
                return redirect(url_for('main'))
            else:
                error = e
                username = request.form['username']
                email = request.form['email']
                password = request.form['password']
                password_confirm = request.form['password_confirm']
        return render_template('register.html', username=username, email=email, password=password, password_confirm=password_confirm, err=error)
    
    @app.route("/logout")
    def logout_page():
        session.pop('username', None)
        return redirect(url_for('login_page'))

    @socketio.on('join')
    def handle_join():
        messages = db_handler.get_recent_messages()
        for message in reversed(messages):
            emit("message", f"{message[0]}: {message[1]}")

    @socketio.on('msg')
    def handle_message(data):
        db_handler.add_message(session['username'], data)
        emit("message", f"{session['username']}: {data}", broadcast=True)  # Send to everyone

    return app