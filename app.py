from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort
import os

from fbchat import Client
from fbchat.models import *

from apscheduler.schedulers.background import BackgroundScheduler

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField, DateTimeField
from wtforms.validators import DataRequired

import datetime as dt
from datetime import datetime

app = Flask(__name__)
scheduler = BackgroundScheduler()

client = None
friends = None
queue = None

# Background Job
def check_for_jobs():
    # if client:
        # client.send(Message(text='Message using cookies'), thread_id='100000046489168', thread_type=ThreadType.USER)
    if queue:
        print(queue)
    print('I am working...')

scheduler.add_job(check_for_jobs, 'interval', seconds=5)
scheduler.start()

# User input form
class UserInput(FlaskForm):
    # name = StringField('Username', validators=[DataRequired()])
    friends = SelectField('Friends', validators=[DataRequired()])
    message = TextAreaField('Message', validators=[DataRequired()])
    timestamp = DateTimeField(label='Date', default=datetime.today, format='%Y-%m-%d %H:%M:%S')
    sendbtn = SubmitField('Send', render_kw={"data-animation": "ripple"})

# Queue for jobs
class Queue:
    def __init__(self):
        self.queue = []

    def add_job(self, username, pw, recipient_uid, message, timestamp):
        self.queue.append({
            'username': username,
            'pw': pw,
            'recipient_uid': recipient_uid,
            'message': message, 
            'timestamp': timestamp
            })

    def __str__(self):
        return str(self.queue)


@app.route("/send/", methods=['POST'])
def send():
    global queue
    global client
    data_form = {}
    for key, value in request.form.items():
        data_form[key] = value

    friend_id = data_form['friends']
    message = data_form['message']
    timestamp = data_form['timestamp']
    # client.send(Message(text=message), thread_id='100000007282966', thread_type=ThreadType.USER)
    queue.add_job(client.email, client.password, friend_id, message, timestamp)
    print(client.email, client.password, friend_id, message, timestamp)
    return redirect('/')

@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        global friends
        form = UserInput()
        form.friends.choices = [(friend.uid, friend.name) for friend in friends]
        return render_template('user_input.html', form=form, friends=friends)

@app.route('/login', methods=['POST'])
def do_admin_login():
    username = request.form['username']
    password = request.form['password']
    try:
        global client
        global friends
        client = Client(username, password, max_tries=1)
        friends = client.fetchAllUsers()
        session['logged_in'] = True
    except FBchatException as exception:
        print(exception)
        flash('wrong password')
    return redirect('/')

@app.route("/logout")
def logout():
    session['logged_in'] = False
    return home()

if __name__ == "__main__":
    queue = Queue()
    app.secret_key = os.urandom(12)
    app.run(debug=True,host='0.0.0.0', port=4000)

