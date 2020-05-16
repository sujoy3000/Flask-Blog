from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy # we are using SQLAlchemy to connect our flask-app with the
from werkzeug import secure_filename  # using for file uploader security
import os # using for file uploader path
import json
import math # To get the last page
from flask_mail import Mail
from datetime import datetime

# understanding pending
import socket
socket.getaddrinfo('localhost', 8080)

''' The JSON format is often used for serializing and transmitting structured data over a network connection.
    It is used primarily to transmit data between a server and web application, serving as an alternative to XML.
    JSON is JavaScript Object Notation. '''

''' we will read all the parameters from the json file'''

with open('config.json', 'r') as c:
    parameters = json.load(c)["params"]     # The params data from json file is now present in parameters

local_server = True


app=Flask(__name__)


# This is for our app's security
app.secret_key = 'super secret key'


app.config['UPLOAD_FOLDER'] = parameters['upload_location']  # For file uploader setting the location to save the uploaded file

# we have to allow on this: https://myaccount.google.com/lesssecureapps
#we are using smtp server of gmail to send the data to our mail
app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = parameters['gmail-user'],
    MAIL_PASSWORD = parameters['gmail-password']
)
mail = Mail(app)



''' If We are using local server then the SQLALCHEMY_DATABASE_URI will be setted as local_uri, otherwise
    if we are using production's uri the SQLALCHEMY_DATABASE_URI will be setted as  prod_uri'''
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = parameters['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = parameters['prod_uri']



db = SQLAlchemy(app)    #initialization


# This class defines the contacts tables of our database
class Contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80),  nullable=False) # nullable = False means user can't left it empty
    phone_num = db.Column(db.String(12),  nullable=False)
    msg = db.Column(db.String(120),  nullable=False)
    date = db.Column(db.String(12),  nullable=True)
    email = db.Column(db.String(20),  nullable=False)


# This class defines the Posts tables of our database
class Posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80),  nullable=False) # nullable = False means user can't left it empty
    slug = db.Column(db.String(25),  nullable=False)
    content = db.Column(db.String(120),  nullable=False)
    tagline = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12),  nullable=True)
    img_file = db.Column(db.String(12), nullable=True)


@app.route("/")
def Home():
    # Fetching all the posts from the database and storing in the variable posts
    posts = Posts.query.filter_by().all()

    #calculating the no of pages
    last = math.ceil( len( posts)/int( parameters['no_of_posts'] ) )

    # Pagination logic
    page = request.args.get( 'page' )

    if (not str(page).isnumeric()):
        page = 1

    page = int( page )

    posts = posts[ (page-1) * int( parameters['no_of_posts'] ): (page-1) * int( parameters['no_of_posts'] ) + int( parameters['no_of_posts'] ) ]

    if page == 1:
        prev = "#"
        next = "/?page=" + str( page + 1 )


    elif page == last:
        prev = "/?page=" + str( page - 1 )
        next = "#"

    else:
        prev = "/?page=" + str( page - 1 )
        next = "/?page=" + str( page + 1 )

    return render_template('index.html', paramet=parameters, posts=posts, prev = prev, next = next)


@app.route("/about")
def About():
    return render_template('about.html', paramet=parameters)


@app.route("/login", methods=['GET', 'POST'])
def Dashbord():

    #if the user is already logged in then there is no need of post request, we'll give him access
    if ('user' in session and session['user'] == parameters['admin_user']):
        # Fetching all the posts from the database and storing in the variable posts
        posts = Posts.query.all()
        return render_template('dashboard.html', paramet = parameters, posts = posts)

    if request.method=='POST':
        # fetching uname and pass  from the form and storing in local variables
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if(username == parameters['admin_user'] and userpass == parameters['admin_password']):
            #Set the session veriable means make the user logged in
            #session['user'] means current session's user
            session['user'] = username
            # Fetching all the posts from the database and storing in the variable posts
            posts = Posts.query.all()
            return render_template('dashboard.html', paramet=parameters, posts = posts)

    # redirect to admin panel
    return render_template('login.html', paramet=parameters)


@app.route( "/edit/<string:sno>", methods = ['GET', 'POST'] )
def edit(sno):
    if( 'user' in session and session['user'] == parameters['admin_user'] ) :
        if request.method == 'POST':
            box_title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            # Now if sno is 0 then we'll give the access to add a new post , otherwise we'll give the access to edit an existing post
            if sno == '0':
                #Creating a new row in the post table of our database with the user's given values
                post = Posts( title = box_title , slug = slug , content = content , tagline = tline, img_file = img_file, date = date )
                db.session.add( post )
                db.session.commit()

            else:
                #Fetching the row of the post table in our database which sno is matching with user's given sno, and storing it in the variable post
                post = Posts.query.filter_by(sno = sno).first()
                #changing the values by user's given values
                post.title = box_title
                post.slug = slug
                post.content = content
                post.tagline = tline
                post.img_file = img_file
                post.date = date
                # to commiting(saving) the data
                db.session.commit()
                # to redirect the user to his adding page
                return redirect('/edit/' + sno)

        post = Posts.query.filter_by(sno=sno).first()
        return  render_template('edit.html', paramet = parameters, post = post, sno = sno )



@app.route("/uploader", methods = {'GET', 'POST'})
def uploader():
    if request.method == "POST":
        #fetching the file
        f = request.files['file1']
        #saving the file in the given folder
        f.save(os.path.join( app.config["UPLOAD_FOLDER"], secure_filename(f.filename)))
        return  "Uploaded Successfully"



@app.route("/logout")
def logout():
    # we'll kill the session variable, here our session variable was user, so we'll kill user
    session.pop('user')
    
    return redirect('/')


@app.route("/delete/<string:sno>", methods = ['GET', 'POST'] )
def delete(sno):
    if ( 'user' in session and session['user'] == parameters['admin_user'] ):
        post = Posts.query.filter_by( sno = sno ).first()
        db.session.delete( post )
        db.session.commit()

    return redirect('/login')


# If we are fetching any file from server or any file like index.html by putting URL, that will happen by GET method
@app.route("/contact", methods = {'GET', 'POST'})
def Contact():
    if(request.method == 'POST'):   # our form will sent a post request to a page and that page will submit all the values

        #Fetching entry

        # Fetching name, email, phone, message from the form and storing in local variables
        name=request.form.get('name')
        email=request.form.get('email')  #here we use the name from template
        phone=request.form.get('phone')
        message=request.form.get('message')

        #Adding Entry to the database

        entry = Contacts( name=name, phone_num=phone, msg=message, date=datetime.now(), email=email )   # entry = class_name( values )
        db.session.add(entry)
        db.session.commit()

        # To send mail to us
        mail.send_message('New Message From ' + name,
                          sender = email,
                          recipients = [parameters['gmail-user']],
                          body = message + "\n" + phone
                          )

    return render_template('contact.html', paramet=parameters)


@app.route("/post/<string:post_slug>", methods=['GET'])     # When user search  HelloProgrammar/post/post's slug   then the post's slug will be store in the variable post_slug
def Post(post_slug):  # we have to pass the variable through the function also

    # Fetching all the posts from the database and storing in the variable post
    post = Posts.query.filter_by(slug=post_slug).first()   # we will fetch the posts according to the searched slugs from the database
                                                           # and store it in the variable post, here we will avoid two slugs with
                                                           # same name, if there are two slugs with the same name in the database then take the first one

    return render_template('post.html', paramet=parameters, post=post)


app.run(debug=True)
