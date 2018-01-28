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

import time

app = Flask(__name__)
scheduler = BackgroundScheduler()

queue = None

# Background Job
def check_for_jobs():
    print('I am working...')
    print("original queue:")
    print(queue)
    print("jobs to send")    
    jobs_to_send = queue.get_jobs()
    for job in jobs_to_send:
        print("sending", job)
        job_client = Client(job['username'], job['pw'])
        job_client.send(Message(text=job['message']), thread_id=job['recipient_uid'], thread_type=ThreadType.USER)

    print("queue after:")
    print(queue)

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

    def get_jobs(self):
        threshold = 500
        jobs_to_send = []
        current_time = int(time.mktime(time.localtime()))

        for job in self.queue:
            job_time = int(time.mktime(time.strptime(job['timestamp'], "%Y-%m-%d %H:%M:%S")))
            diff_time = job_time - current_time
            if diff_time < 60:
                jobs_to_send.append(job)
                self.queue.remove(job)

        return jobs_to_send

    def __str__(self):
        return str(self.queue)


@app.route("/send/", methods=['POST'])
def send():
    global queue

    data_form = {}
    for key, value in request.form.items():
        data_form[key] = value

    friend_id = data_form['friends']
    message = data_form['message']
    timestamp = data_form['timestamp']
    queue.add_job(session['username'], session['password'], friend_id, message, timestamp)
    return redirect('/')

@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        username = session['username']
        password = session['password']
        session_client = Client(username, password)        
        friends = session_client.fetchAllUsers()
        friends = [{'name':friend.name, 'uid':friend.uid} for friend in friends]
        friends = sorted(friends, key=lambda k: k['name'])

        form = UserInput()
        form.friends.choices = [(friend['uid'], friend['name']) for friend in friends]
        session_client.logout()
        return render_template('user_input.html', form=form, friends=friends)

@app.route('/login', methods=['POST'])
def do_admin_login():
    try:
        username = request.form['username']
        password = request.form['password']

        session['username'] = username
        session['password'] = password

        client = Client(username, password, max_tries=1)
        friends = client.fetchAllUsers()
        friends = [{'name':friend.name, 'uid':friend.uid} for friend in friends]
        friends = sorted(friends, key=lambda k: k['name'])
        session['logged_in'] = True
        client.logout()
    except FBchatException as exception:
        print(exception)
        flash('wrong password')
    return home()

@app.route("/logout")
def logout():
    session['logged_in'] = False
    session['username'] = None
    session['password'] = None
    return home()

if __name__ == "__main__":
    queue = Queue()
    app.secret_key = os.urandom(12)
    app.run(debug=True,host='0.0.0.0', port=5000)

