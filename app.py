from flask import Flask,render_template,request,flash,redirect,session
# flash is used to display messages
import werkzeug.utils
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from flask_mail import Mail
import os
import math
import json
from datetime import datetime

with open('config.json', 'r') as c:
    params = json.load(c)["params"]

app = Flask(__name__)
app.secret_key = "super-secret-key"

app.config.update(
    MAIL_SERVER = "smtp.gmail.com",
    MAIL_PORT = "465",
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params["gmail-user"],
    MAIL_PASSWORD = params["gmail-password"]

)
mail = Mail(app)

app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']

db = SQLAlchemy(app)
class Contacts(db.Model):
    sno = db.Column(db.Integer,primary_key = True, autoincrement=True)
    name = db.Column(db.String(80),nullable = False)
    phone_num = db.Column(db.String(12),nullable = False)
    email = db.Column(db.String(20),nullable = False)
    msg = db.Column(db.String(120),nullable = False)
    date = db.Column(db.String(12),nullable = True)

class Posts(db.Model):
    sno = db.Column(db.Integer,primary_key = True, autoincrement=True)
    title = db.Column(db.String(100),nullable = False)
    author = db.Column(db.String(20),nullable = False)
    first_published = db.Column(db.String(7),nullable = True)
    genre = db.Column(db.String(20),nullable = False)
    about_author = db.Column(db.Text,nullable = True)
    buy_link = db.Column(db.Text,nullable = True)
    quote = db.Column(db.String(500),nullable = True)
    quoted_by = db.Column(db.String(25),nullable = True)
    content = db.Column(db.Text, nullable = False)
    date = db.Column(db.String(20),nullable = True)
    slug = db.Column(db.String(20),nullable = False)

@app.route('/')
def home():
    posts = Posts.query.filter_by().order_by(desc(Posts.sno)).all()
    last = math.ceil(len(posts)/int(params['no_of_posts']))
    page = request.args.get('page')
    if (not str(page).isnumeric()):
        page = 1
    page = int(page)
    posts = posts[(page-1)*int(params['no_of_posts']) : (page-1)*int(params['no_of_posts']) + int(params['no_of_posts'])]

    if page == 1:
        prev = "#"
        next = "/?page=" + str(page+1)

    elif page == last:
        prev = "/?page=" + str(page-1)
        next = "#"

    else:
        prev = "/?page=" + str(page-1)
        next = "/?page=" + str(page+1)

    return render_template('index.html',params = params, posts = posts, prev = prev, next = next)

@app.route("/post/<string:post_slug>", methods = ['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(slug = post_slug).first()
    return render_template('post.html',post = post,params = params)

@app.route('/about')
def about():
    return render_template('about.html', params = params)

@app.route('/dashboard', methods = ['GET','POST'])
def dashboard():
    if 'user' in session and session['user'] == params['admin_user']:  # user authentication
        posts = Posts.query.all()
        return render_template('dashboard.html', params = params,posts = posts)

    if request.method == 'POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if username == params['admin_user'] and userpass == params['admin_password'] :
            # set session variable
            session['user'] = username    # logging in
            posts = Posts.query.all()
            return render_template('dashboard.html',params = params,posts = posts)

    return render_template('login.html',params = params)  

@app.route('/edit/<string:sno>', methods = ['GET','POST'])
def edit(sno):
    if 'user' in session and session['user'] == params['admin_user']:  # user authentication
        if request.method == 'POST':
            title = request.form.get('title')
            slug = request.form.get('slug')
            content = request.form.get('content')
            author = request.form.get('author')
            first_published = request.form.get('first_published')
            genre = request.form.get('genre')
            about_author = request.form.get('about_author')
            buy_link = request.form.get('buy_link')
            quote = request.form.get('quote')
            quoted_by = request.form.get('quoted_by')
            date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            if sno == '0':     # means no post present in database
                post = Posts(title = title,slug = slug, content = content, date = date,author = author,first_published = first_published, genre = genre, about_author = about_author, buy_link = buy_link, quote = quote, quoted_by = quoted_by)
                db.session.add(post)   # adding new post to database
                db.session.commit()
            else:             # editing a pre-existing post
                post = Posts.query.filter_by(sno = sno).first()
                post.title = title
                post.slug = slug
                post.content = content
                post.date = date
                post.author = author
                post.first_published = first_published
                post.genre = genre
                post.about_author = about_author
                post.buy_link = buy_link
                post.quote = quote
                post.quoted_by = quoted_by
                db.session.commit()
                
                return redirect('/edit/' + sno)  # redirecting to edited post
        post = Posts.query.filter_by(sno = sno).first()
        return render_template('edit.html',params = params, post = post,sno = sno)

@app.route('/logout')
def logout():
    session.pop('user')             # killing the login session
    return redirect('/dashboard')

@app.route('/delete/<string:sno>', methods = ['GET','POST'])
def delete(sno):
    if 'user' in session and session['user'] == params['admin_user']:
        post = Posts.query.filter_by(sno = sno).first()
        if post:
            deleted_sno = post.sno  # Get the 's.no' of the post to be deleted
            db.session.delete(post)
            db.session.commit()

            # Decrement the 's.no' values for remaining posts
            remaining_posts = Posts.query.filter(Posts.sno > deleted_sno)
            for post in remaining_posts:
                post.sno -= 1
        db.session.commit()
    return redirect('/dashboard')


@app.route('/contact', methods = ['GET','POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name = name, phone_num = phone,email = email,msg = message,datetime = datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New message from ' + name, sender = email,recipients = [params['gmail-user']], body = message + "\n"+ phone)
    return render_template('contact.html', params = params)



if __name__ == "__main__":
    app.run(port = 5500, debug = True)