from flask import Flask, render_template, request, url_for, redirect, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import delete,desc
import sqlite3
import os
from datetime import datetime
from sqlalchemy.exc import IntegrityError

current_dir=os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.abspath('static')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app = Flask(__name__,static_folder=os.path.abspath('static'))
app.app_context().push()
app.config['SQLALCHEMY_DATABASE_URI']= 'sqlite:///db.sqlite3'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY']='secretkey'
db=SQLAlchemy(app)

class users(db.Model):
    _id=db.Column(db.Integer,autoincrement=True)
    username=db.Column(db.String(100),primary_key=True,nullable=False)
    name=db.Column(db.String(100),nullable=False)
    password=db.Column(db.String(100),nullable=False)

    def __init__(self,username,name,password):
        self.username=username
        self.name=name
        self.password=password

class users_posts(db.Model):
    _id=db.Column("id",db.Integer,primary_key=True)
    whos_post=db.Column(db.String(100),db.ForeignKey('users.username'),nullable=False)
    img_addr=db.Column(db.String(100),nullable=False)
    img_name=db.Column(db.String(100),nullable=False)
    timestamp=db.Column(db.DateTime,nullable=False,default=datetime.utcnow)
    caption=db.Column(db.String(100),nullable=False)
    title=db.Column(db.String(100),nullable=False)

    def __init__(self,whos_post,img_addr,img_name,caption,title):
        self.whos_post=whos_post
        self.img_addr=img_addr
        self.img_name=img_name
        self.caption=caption
        self.title=title

class who_follow(db.Model):
    _id=db.Column("id",db.Integer,primary_key=True)
    who=db.Column(db.String(100),db.ForeignKey('users.username'),nullable=False)
    follows=db.Column(db.String(100),db.ForeignKey('users.username'),nullable=False)
    __table_args__ = (db.UniqueConstraint('who', 'follows', name='_who_follows_uc'),)

    def __init__(self,who,follows):
        self.who=who
        self.follows=follows

@app.route('/')
def first_page():
    return render_template("Login_sign_up.html")

@app.route('/',methods=["POST"])
def login():
    usrnm1=request.form['usrnm']
    pw1=request.form['pw']
    cur_user=users.query.filter_by(username=usrnm1).first()
    if cur_user and cur_user.password==pw1:
        return redirect(url_for('Feed',name=cur_user.username))
    elif cur_user==None:
        return render_template('temp.html',error_message="User does not exist, please sign up")
    else:
        return render_template('temp.html',error_message="Incorrect Password")


@app.route('/Signup')
def signup():
    return render_template("Sign_up.html")

@app.route('/Signup',methods=["POST"])
def store_new_user():
    cur_username=request.form["usrnm"]
    cur_name=request.form["Name"]
    passwd=request.form["pw"]
    passwd1=request.form["pw1"]
    if passwd==passwd1:
        try:
            usr=users(cur_username,cur_name,passwd)
            db.session.add(usr)
            db.session.commit()
            return redirect(url_for('Feed',name=cur_username))
        except IntegrityError:
            return render_template('temp.html',error_message="Username is taken")
    return render_template("temp.html",error_message="Passwords do not match")

@app.route('/Feed/<name>')
def Feed(name):
    res = [r.follows for r in who_follow.query.filter_by(who=name).all()]
    res.append(name)
    post1=users_posts.query.filter(users_posts.whos_post.in_(res)).order_by(desc(users_posts.timestamp)).all()
    return render_template('feed.html',cur_profile=name,posts=post1)

@app.route('/add_post/<name>')
def add_post_page(name):
    return render_template('add_post.html',name_user=name)

@app.route('/add_post/<name>',methods=["POST"])
def store_in_db(name):
    image=request.files["image"]
    image.save(os.path.join(app.config['UPLOAD_FOLDER'], image.filename))
    image_file=url_for('static',filename=image.filename)
    cur_caption=request.form["caption"]
    tit=request.form["title"]
    post=users_posts(name,image_file,image.filename,cur_caption,tit)
    db.session.add(post)
    db.session.commit()
    return redirect(url_for('Feed',name=name))

@app.route('/other_profile/<name>/<o_name>')
def other_profile(name,o_name):
    followers=who_follow.query.filter_by(follows=o_name).all()
    following=who_follow.query.filter_by(who=o_name).all()
    cur_user=users_posts.query.filter_by(whos_post=o_name).all()
    cur_user_following=who_follow.query.filter_by(who=name).all()
    return render_template("otheruser_profile.html",user_name=o_name, posts_sent=cur_user, length=len(cur_user),
                            followers_l=len(followers),
                            following_l=len(following),
                            following_v=cur_user_following
                                ,cur=name)

@app.route('/follow/<who_isfollowing>/<follows>')
def follow(who_isfollowing,follows):
    try:
        row=who_follow(who_isfollowing,follows)
        db.session.add(row)
        db.session.commit()
        followers=who_follow.query.filter_by(follows=follows).all()
        following=who_follow.query.filter_by(who=follows).all()
        cur_user=users_posts.query.filter_by(whos_post=follows).all()
        cur_user_following=who_follow.query.filter_by(who=who_isfollowing).all()
        return render_template("otheruser_profile.html",user_name=follows, posts_sent=cur_user, length=len(cur_user),
                                followers_l=len(followers),
                                following_l=len(following),
                                following_v=cur_user_following
                                    ,cur=who_isfollowing)
    except IntegrityError:
        db.session.rollback()
        followers=who_follow.query.filter_by(follows=follows).all()
        following=who_follow.query.filter_by(who=follows).all()
        cur_user=users_posts.query.filter_by(whos_post=follows).all()
        cur_user_following=who_follow.query.filter_by(who=who_isfollowing).all() 
        return render_template("otheruser_profile.html",user_name=follows, posts_sent=cur_user, length=len(cur_user),
                                followers_l=len(followers),
                                following_l=len(following),
                                following_v=cur_user_following
                                    ,cur=who_isfollowing)

@app.route('/unfollow/<who_isunfollowing>/<follows>')
def unfollow(who_isunfollowing,follows):
    who_follow.query.filter_by(who=who_isunfollowing,follows=follows).delete()
    db.session.commit()
    followers=who_follow.query.filter_by(follows=follows).all()
    following=who_follow.query.filter_by(who=follows).all()
    cur_user=users_posts.query.filter_by(whos_post=follows).all()
    cur_user_following=who_follow.query.filter_by(who=who_isunfollowing).all()
    return render_template("otheruser_profile.html",user_name=follows, posts_sent=cur_user, length=len(cur_user),
                                followers_l=len(followers),
                                following_l=len(following),
                                following_v=cur_user_following
                                    ,cur=who_isunfollowing)

@app.route('/search/<name>',methods=["GET","POST"])
def search(name):
    if request.method=="POST":
        search_for=request.form['enterusername']
        search_format = "%{}%".format(search_for)
        res=[r.username for r in users.query.filter(users.username.like(search_format)).all()] 
        return render_template('search_results.html',sent_users=res,cur_user=name)
    else:
        return render_template('temp.html',error_message="No users found")

@app.route('/display/<cur_user>/<name>/<action>')
def display(cur_user,name,action):
    if action=='followers':
        res=[r.who for r in who_follow.query.filter_by(follows=name).all()]
        return render_template('search_results.html',sent_users=res,cur_user=cur_user)
    else:
        res=[r.follows for r in who_follow.query.filter_by(who=name).all()]
        return render_template('search_results.html',sent_users=res,cur_user=cur_user) 

@app.route('/edit/<name>/<id>',methods=["GET","POST"])
def edit(name,id):
    pic=users_posts.query.filter_by(_id=id).all()
    return render_template('edit.html',name=name,id=id,photo=pic)

@app.route('/delete/<name>/<id>',methods=["GET","POST"])
def delete(name,id):
    img_name=users_posts.query.filter_by(_id=id).first()
    os.remove(os.path.join(UPLOAD_FOLDER,img_name.img_name))
    users_posts.query.filter_by(_id=id).delete()
    db.session.commit()
    return redirect(url_for('Feed',name=name))

@app.route('/ac_edit/<name>/<id>',methods=["GET","POST"])
def ac_edit(name,id):
    new_title=request.form['Title']
    new_caption=request.form['caption']
    post=users_posts.query.filter_by(_id=id).first()
    post.title=new_title
    post.caption=new_caption
    db.session.commit()
    return redirect(url_for('Feed',name=name))

@app.route('/reset_password',methods=["GET","POST"])
def reset_password():
    get_name=request.form['name']
    get_user=users.query.filter_by(username=get_name).first()
    new_pw=request.form['new_pw']
    conf_pw=request.form['conf_pw']
    if get_user and new_pw==conf_pw:
        get_user.password=new_pw
        db.session.commit()
        return redirect('/')
    elif new_pw==conf_pw:
        return render_template('temp.html',error_message="User does not exist")
    else:
        return render_template('temp.html',error_message="Passwords do not match")

@app.route('/reset')
def reset():
    return render_template('reset.html')

db.create_all()
app.run(debug=True)