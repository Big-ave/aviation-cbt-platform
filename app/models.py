from datetime import datetime
from flask_login import UserMixin
from . import db
class User(UserMixin,db.Model):
 id=db.Column(db.Integer,primary_key=True); username=db.Column(db.String(80),unique=True,nullable=False); email=db.Column(db.String(160),unique=True,nullable=False); password_hash=db.Column(db.String(255),nullable=False); is_admin=db.Column(db.Boolean,default=False); active=db.Column(db.Boolean,default=True); created_at=db.Column(db.DateTime,default=datetime.utcnow)
class Category(db.Model):
 id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(120),unique=True,nullable=False); description=db.Column(db.Text,default=''); active=db.Column(db.Boolean,default=True)
class Exam(db.Model):
 id=db.Column(db.Integer,primary_key=True); name=db.Column(db.String(160),nullable=False); description=db.Column(db.Text,default=''); category_id=db.Column(db.Integer,db.ForeignKey('category.id'),nullable=False); duration_minutes=db.Column(db.Integer,default=30); pass_mark=db.Column(db.Float,default=70); questions_per_attempt=db.Column(db.Integer,default=20); randomize_questions=db.Column(db.Boolean,default=True); randomize_options=db.Column(db.Boolean,default=False); show_answers_after_submission=db.Column(db.Boolean,default=True); active=db.Column(db.Boolean,default=True); category=db.relationship('Category',backref='exams')
class Question(db.Model):
 id=db.Column(db.Integer,primary_key=True); exam_id=db.Column(db.Integer,db.ForeignKey('exam.id'),nullable=False); number=db.Column(db.Integer,nullable=False); text=db.Column(db.Text,nullable=False); option_a=db.Column(db.Text,nullable=False); option_b=db.Column(db.Text,nullable=False); option_c=db.Column(db.Text,nullable=False); option_d=db.Column(db.Text); correct_answer=db.Column(db.String(1)); explanation=db.Column(db.Text,default=''); difficulty=db.Column(db.String(30),default='Medium'); active=db.Column(db.Boolean,default=True); exam=db.relationship('Exam',backref='questions')
class Attempt(db.Model):
 id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False); exam_id=db.Column(db.Integer,db.ForeignKey('exam.id'),nullable=False); started_at=db.Column(db.DateTime,default=datetime.utcnow); submitted_at=db.Column(db.DateTime); duration_seconds=db.Column(db.Integer,default=0); score=db.Column(db.Integer,default=0); total=db.Column(db.Integer,default=0); percentage=db.Column(db.Float,default=0); status=db.Column(db.String(20),default='IN_PROGRESS'); user=db.relationship('User',backref='attempts'); exam=db.relationship('Exam',backref='attempts')
class UserAnswer(db.Model):
 id=db.Column(db.Integer,primary_key=True); attempt_id=db.Column(db.Integer,db.ForeignKey('attempt.id'),nullable=False); question_id=db.Column(db.Integer,db.ForeignKey('question.id'),nullable=False); selected_answer=db.Column(db.String(1)); question=db.relationship('Question'); attempt=db.relationship('Attempt',backref='answers')
