from flask import Flask,render_template,request,session,redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from sqlalchemy import text 
import json
from flask_mail import Mail
from datetime import datetime
import os

local_server=True
with open('config.json','r') as f:
    params=json.load(f)["params"]

app = Flask(__name__)
app.config['UPLOAD_FOLDER']=params['upload_location']
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-pass']
)
mail=Mail(app)
app.secret_key = params['secret_key']
if(local_server):
    app.config["SQLALCHEMY_DATABASE_URI"] = params['local_uri']
else:
    app.config["SQLALCHEMY_DATABASE_URI"]=params['prod_uri']
db=SQLAlchemy(app)

@app.context_processor
def inject_now():
    return {'year': datetime.now().year}

@app.context_processor
def inject_now():
    return {'now': datetime.now()}

class Posts(db.Model):
    __tablename__='posts'
    SNo = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(20), nullable=False)
    content = db.Column(db.String(120), nullable=False)
    tagline = db.Column(db.String(80), nullable=False)
    postedby = db.Column(db.String(25), nullable=False)
    date = db.Column(db.DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    img_file = db.Column(db.String(20), nullable=False)


class Contacts(db.Model):
    __tablename__ = 'contacts'
    SNo = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.Text, nullable=False)
    Phone = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))


@app.route("/", defaults={"page": 1})
@app.route("/page/<int:page>")
def index(page):
    per_page = params['no_of_posts']   # number of posts per page from config
    pagination = Posts.query.order_by(Posts.date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    latest = Posts.query.order_by(Posts.date.desc()).first()
    return render_template('index.html', params=params, posts=pagination.items, latest=latest, pagination=pagination)



@app.route("/login", methods=['GET', 'POST'])
def login():

    if ('user' in session and session['user']==params['admin']):
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username=request.form.get('uname')
        userpass=request.form.get('pass')
        if(username==params['admin'] and userpass==params['admin_pass']):
            session['user']=username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials. Please try again.', 'error')


    return render_template("login.html",params=params)

@app.route("/dashboard")
def dashboard():
    if 'user' not in session or session['user']!=params['admin']:
        flash('Please log in to access the dashboard.','error')
        return redirect(url_for('login'))
    posts=Posts.query.order_by(Posts.date.desc()).all()
    latest = Posts.query.order_by(Posts.date.desc()).first()
    return render_template('dashboard.html',params=params,posts=posts,latest=latest)

@app.route("/edit/<string:sno>",methods=['POST','GET'])
def edit(sno):
    if 'user' not in session or session['user'] != params['admin']:
        flash('Please log in first.', 'error')
        return redirect(url_for('login'))
    post = None
    if sno != "0":  # if editing an existing post
        post = Posts.query.filter_by(SNo=int(sno)).first()

    if request.method == 'POST':
        box_title = request.form.get('title')
        tline = request.form.get('tline')
        slug = request.form.get('slug')
        content = request.form.get('content')
        img_file = request.form.get('img_file')
        postedby = request.form.get('postedby')

        if sno == "0":  # New Post
            post = Posts(title=box_title, slug=slug, content=content,  postedby=postedby ,tagline=tline, img_file=img_file)
            db.session.add(post)
            db.session.commit()
            flash("New post added successfully!", "success")
        else:  # Edit existing
            post = Posts.query.filter_by(SNo=int(sno)).first()
            if post:
                post.title = box_title
                post.slug = slug
                post.content = content
                post.tagline = tline
                post.img_file = img_file
                db.session.commit()
                flash("Post updated successfully!", "success")

        return redirect(url_for('dashboard'))
    

    # GET request -> render editor
    post = None if sno == "0" else Posts.query.filter_by(SNo=int(sno)).first()
    latest = Posts.query.order_by(Posts.date.desc()).first()   # ✅ ADD THIS
    return render_template('edit.html', params=params, post=post, latest=latest)


@app.route("/about")
def about():
     latest=Posts.query.order_by(Posts.date.desc()).first()
     return render_template('about.html',params=params,latest=latest)

@app.route("/logout")
def logout():
    session.pop('user', None)
    flash("Logged out successfully!", "success")
    return redirect(url_for('login'))


@app.route("/delete/<string:sno>",methods=['POST','GET'])
def delete(sno):
    if('user' in session and session['user']==params['admin']):
        post=Posts.query.filter_by(SNo=int(sno)).first()
        db.session.delete(post)
        db.session.commit()
        flash("Post deleted successfully!", "success")
    else:
        flash("Unauthorized action!", "error")
    return redirect(url_for('dashboard'))

@app.route("/uploader",methods=['POST','GET'])
def uploader():
    if 'user' in session and session['user'] == params['admin']:
        if request.method == 'POST':
            f = request.files['file1']
            filename = secure_filename(f.filename)
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash("File uploaded successfully!", "success")
            return redirect(url_for('dashboard'))
    flash("Unauthorized or invalid request!", "error")
    return redirect(url_for('login'))


@app.route("/contact",methods=['POST','GET'])
def contact():
     latest = Posts.query.order_by(Posts.date.desc()).first()
     if (request.method=='POST'):
         print("Form submitted")
         print(request.form)
         name=request.form.get('name')
         email=request.form.get('email')
         phone=request.form.get('phone')
         message=request.form.get('message')

         entry=Contacts(Name=name,Phone=phone,email=email,message=message)
         try:
            db.session.add(entry)
            db.session.commit()

            try:
                mail.send_message('new message from '+name,sender=params['gmail-user'],
                recipients=[params['gmail-user']],
                body=message+"\n"+phone
                )
                print("Mail sent!")
            except Exception as e:
                print("Mail Error:",e)

            print("submitted to db")
         except Exception as e:
             db.session.rollback()
             print("db error",e)
             print("Error: ",e)
     return render_template('contact.html',params=params,latest=latest)

@app.route("/post/<string:post_slug>",methods=['GET'])
def post(post_slug):
    post2=Posts.query.filter_by(slug=post_slug).first()
    latest = Posts.query.order_by(Posts.date.desc()).first()
    return render_template('post.html',params=params,post=post2,latest=latest)

with app.app_context():
    db.create_all()
app.run(debug=True)