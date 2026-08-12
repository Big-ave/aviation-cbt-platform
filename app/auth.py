from flask import Blueprint,request,redirect,url_for,flash
from flask_login import login_user,logout_user,login_required,current_user
from werkzeug.security import generate_password_hash,check_password_hash
from . import db
from .models import User
auth_bp=Blueprint('auth',__name__)
PAGE='''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>AeroCBT</title><style>body{font-family:Arial;background:#0b1220;color:#fff;max-width:700px;margin:40px auto;padding:20px}input,button{padding:12px;margin:6px 0;width:100%;box-sizing:border-box}button{background:#2563eb;color:white;border:0;border-radius:8px}a{color:#93c5fd}</style></head><body>{% with messages=get_flashed_messages() %}{% for m in messages %}<p>{{m}}</p>{% endfor %}{% endwith %}{{body|safe}}</body></html>'''
def page(body):
 from flask import render_template_string
 return render_template_string(PAGE,body=body)
@auth_bp.route('/login',methods=['GET','POST'])
def login():
 if current_user.is_authenticated:return redirect(url_for('main.dashboard'))
 if request.method=='POST':
  u=User.query.filter_by(username=request.form.get('username','').strip()).first()
  if u and u.active and check_password_hash(u.password_hash,request.form.get('password','')):login_user(u);return redirect(url_for('main.dashboard'))
  flash('Invalid username or password.')
 return page('<h1>AeroCBT Login</h1><form method="post"><input name="username" placeholder="Username"><input type="password" name="password" placeholder="Password"><button>Login</button></form><a href="/register">Create account</a>')
@auth_bp.route('/register',methods=['GET','POST'])
def register():
 if request.method=='POST':
  username=request.form.get('username','').strip(); email=request.form.get('email','').strip().lower(); password=request.form.get('password','')
  if len(password)<6: flash('Password must be at least 6 characters.')
  elif User.query.filter((User.username==username)|(User.email==email)).first(): flash('Username or email already exists.')
  else: db.session.add(User(username=username,email=email,password_hash=generate_password_hash(password)));db.session.commit();flash('Registration successful.');return redirect(url_for('auth.login'))
 return page('<h1>Create account</h1><form method="post"><input name="username" placeholder="Username"><input name="email" type="email" placeholder="Email"><input name="password" type="password" placeholder="Password"><button>Register</button></form><a href="/login">Login</a>')
@auth_bp.route('/logout')
@login_required
def logout():logout_user();return redirect(url_for('auth.login'))
