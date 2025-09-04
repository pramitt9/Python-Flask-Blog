from flask import Flask,render_template,request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text 
import json
from flask_mail import Mail

local_server=True
with open('config.json','r') as f:
    params=json.load(f)["params"]

app = Flask(__name__)
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-pass']
)
mail=Mail(app)
if(local_server):
    app.config["SQLALCHEMY_DATABASE_URI"] = params['local_uri']
else:
    app.config["SQLALCHEMY_DATABASE_URI"]=params['prod_uri']
db=SQLAlchemy(app)

class Posts(db.Model):
    __tablename__='posts'
    SNo = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(20), nullable=False)
    content = db.Column(db.String(120), nullable=False)
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


@app.route("/")
def index():
    posts=Posts.query.all()
    latest=Posts.query.order_by(Posts.date.desc()).first()
    return render_template('index.html',params=params,posts=posts,latest=latest)

@app.route("/about")
def about():
    return render_template('about.html',params=params)

@app.route("/contact",methods=['POST','GET'])
def contact():
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
     return render_template('contact.html',params=params)

@app.route("/post/<string:post_slug>",methods=['GET'])
def post(post_slug):
    post2=Posts.query.filter_by(slug=post_slug).first()
    latest = Posts.query.order_by(Posts.date.desc()).first()
    return render_template('post.html',params=params,post=post2,latest=latest)

with app.app_context():
    db.create_all()
app.run(debug=True)