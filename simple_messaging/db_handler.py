import sqlite3
from flask import current_app, g
from datetime import datetime

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    db_con = get_db()
    with current_app.open_resource('schema.sql') as f:
        db_con.executescript(f.read().decode('utf8'))
    db_con.commit()

sqlite3.register_converter(
    "timestamp", lambda v: datetime.fromisoformat(v.decode())
)

def add_login(username, email, password, password_confirm):
    if(password != password_confirm):
        return "Passwords do not match!"
    if(username == "" or password == ""):
        return "Please fill in all the fields!"
    
    db = get_db() 
    c = db.cursor()
    d = c.execute("SELECT * from Users WHERE username = ?", [username])
    if d.fetchone() is not None:
        return "That username is taken."
    d = c.execute("SELECT * from Users WHERE email = ?", [email])
    if d.fetchone() is not None:
        return "That email is already in use."
    

    c.execute("INSERT INTO Users (username, email, pass) VALUES(?, ?, ?)", [username, email, password])
    db.commit()
    


def validate_login(username, password):
    if(username == '' or password == ''):
        return "Invalid username or password"
    
    db = get_db()
    c = db.cursor()

    d = c.execute("SELECT * FROM Users WHERE username = ? AND pass = ?", [username, password])
    if d.fetchone() is None:
        return "Invalid username or password"

def add_message(username, content):
    db = get_db()
    c = db.cursor()

    uid = c.execute("SELECT id FROM Users WHERE username = ?", [username]).fetchone()[0]
    c.execute("INSERT INTO Messages (userid, content) VALUES(?, ?)", [uid, content])
    db.commit()

def get_recent_messages():
    db = get_db()
    c = db.cursor()

    msg = c.execute("SELECT Users.username, Messages.content, Messages.created FROM Messages JOIN Users ON Users.id=Messages.userid ORDER BY created DESC LIMIT 50").fetchall()

    return msg