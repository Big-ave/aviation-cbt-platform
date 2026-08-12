from pathlib import Path
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from werkzeug.security import generate_password_hash

db=SQLAlchemy(); login_manager=LoginManager(); login_manager.login_view='auth.login'

def create_app():
    app=Flask(__name__,instance_relative_config=True); Path(app.instance_path).mkdir(parents=True,exist_ok=True)
    app.config['SECRET_KEY']=os.environ.get('SECRET_KEY','dev-only-change-me')
    url=os.environ.get('DATABASE_URL') or 'sqlite:///'+str(Path(app.instance_path)/'cbt.db')
    app.config['SQLALCHEMY_DATABASE_URI']=url.replace('postgres://','postgresql://',1) if url.startswith('postgres://') else url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
    db.init_app(app); login_manager.init_app(app)
    from .auth import auth_bp; from .main import main_bp; from .admin import admin_bp
    app.register_blueprint(auth_bp); app.register_blueprint(main_bp); app.register_blueprint(admin_bp)
    with app.app_context(): db.create_all(); seed_data()
    return app
@login_manager.user_loader
def load_user(uid):
    from .models import User
    return db.session.get(User,int(uid))
def seed_data():
    from .models import User,Category,Exam
    if not User.query.filter_by(username='admin').first(): db.session.add(User(username='admin',email='admin@aviationcbt.local',password_hash=generate_password_hash('Admin@123'),is_admin=True))
    for n,d in [('Gas Turbine','Gas turbine engine maintenance and systems.'),('General','General aviation subjects.'),('Pressurised Airframe','Pressurised airframe maintenance subjects.')]:
        if not Category.query.filter_by(name=n).first(): db.session.add(Category(name=n,description=d))
    db.session.flush()
    if not Exam.query.filter_by(name='15.3 GTE - Engine Inlet').first(): db.session.add(Exam(name='15.3 GTE - Engine Inlet',description='Gas Turbine Engine inlet examination.',category_id=Category.query.filter_by(name='Gas Turbine').first().id,duration_minutes=30,pass_mark=70,questions_per_attempt=41,randomize_questions=False,active=True))
    db.session.commit()
