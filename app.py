from flask import Flask
from flask import Flask, flash, redirect, render_template, request, session, abort
import os

from fbchat import Client
from fbchat.models import *
 
app = Flask(__name__)
 
@app.route('/')
def home(facebook_client):
    if facebook_client is None:
        return render_template('login.html')

    friends = facebook_client.fetchAllUsers()
    print(facebook_client)
    for friend in friends:
        print(friend.name)

    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return render_template('friends_list.html', friends=friends)
 
@app.route('/login', methods=['POST'])
def do_admin_login():

    username = request.form['username']
    password = request.form['password']

    try:
        client = Client(username, password, max_tries=1)
        session['logged_in'] = True
        # facebook_client = client
    except FBchatException as exception:
        print(exception)
        flash('wrong password')

    return home(client)

    # if request.form['password'] == 'password' and request.form['username'] == 'admin':
    #     session['logged_in'] = True
    # else:
    #     flash('wrong password!')
    # return home()
    # if request.form['password'] == 'password' and request.form['username'] == 'admin':
    #     session['logged_in'] = True
    # else:
    #     flash('wrong password!')
    # return home()

@app.route("/logout")
def logout():
    session['logged_in'] = False
    return home(None)

 
if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True,host='0.0.0.0', port=4000)
