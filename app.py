from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort
import os

from fbchat import Client
from fbchat.models import *
 
app = Flask(__name__)
 
@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return render_template('friends_list.html')
 
@app.route('/login', methods=['POST'])
def do_admin_login():
    username = request.form['username']
    password = request.form['password']

    try:
        client = Client(username, password, max_tries=1)
        session['logged_in'] = True
        friends = client.fetchAllUsers()
        return render_template('friends_list.html', friends=friends)
    except FBchatException as exception:
        print(exception)
        flash('wrong password')

    return home()

@app.route("/logout")
def logout():
    session['logged_in'] = False
    return home()

 
if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True,host='0.0.0.0', port=4000)
