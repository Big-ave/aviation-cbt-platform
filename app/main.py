from datetime import datetime,timezone
import random
from flask import Blueprint,request,redirect,url_for,session,flash,abort,render_template_string
from flask_login import login_required,current_user
from . import db
from .models import Exam,Question,Attempt,UserAnswer
main_bp=Blueprint('main',__name__)
BASE='''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><title>AeroCBT</title><style>body{font-family:Arial;background:#0b1220;color:#eef2ff;margin:0}main{max-width:1000px;margin:auto;padding:24px}nav{display:flex;gap:16px;flex-wrap:wrap;padding:16px;background:#111827}a{color:#93c5fd}.card{background:#172033;padding:20px;margin:14px 0;border-radius:14px}button{padding:11px 16px;border:0;border-radius:8px;background:#2563eb;color:white;margin:4px}label{display:block;padding:12px;background:#1e293b;margin:8px 0;border-radius:8px}</style></head><body><nav><a href="/dashboard">Dashboard</a><a href="/exams">Exams</a><a href="/history">History</a><a href="/logout">Logout</a></nav><main>{{body|safe}}</main></body></html>'''
def page(body):return render_template_string(BASE,body=body)
@main_bp.route('/')
def index():return redirect(url_for('main.dashboard')) if current_user.is_authenticated else redirect(url_for('auth.login'))
@main_bp.route('/dashboard')
@login_required
def dashboard():
 attempts=Attempt.query.filter_by(user_id=current_user.id,status='SUBMITTED').order_by(Attempt.submitted_at.desc()).limit(10).all()
 exams=Exam.query.filter_by(active=True).all()
 body=f'<h1>Welcome, {current_user.username}</h1><p>AeroCBT Aircraft Engineering Examination Platform</p>'
 for e in exams: body+=f'<div class="card"><h2>{e.name}</h2><p>{e.description}</p><form method="post" action="/exam/{e.id}/start"><button>Start Exam</button></form></div>'
 body+='<h2>Recent Results</h2>'+''.join(f'<div class="card">{a.exam.name}: {a.percentage}% — {a.status}</div>' for a in attempts)
 return page(body)
@main_bp.route('/exams')
@login_required
def exams():return redirect(url_for('main.dashboard'))
@main_bp.route('/exam/<int:exam_id>/start',methods=['POST'])
@login_required
def start_exam(exam_id):
 exam=db.session.get(Exam,exam_id); qs=Question.query.filter_by(exam_id=exam_id,active=True).order_by(Question.number).all()
 if not exam or not qs: flash('This examination has no active questions.');return redirect(url_for('main.dashboard'))
 if exam.randomize_questions:random.shuffle(qs)
 qs=qs[:exam.questions_per_attempt]; a=Attempt(user_id=current_user.id,exam_id=exam.id,started_at=datetime.utcnow(),total=len(qs));db.session.add(a);db.session.flush()
 for q in qs:db.session.add(UserAnswer(attempt_id=a.id,question_id=q.id))
 db.session.commit();session.update(attempt_id=a.id,question_ids=[q.id for q in qs],current_index=0,deadline=datetime.now(timezone.utc).timestamp()+exam.duration_minutes*60);return redirect(url_for('main.take_exam'))
@main_bp.route('/exam/take',methods=['GET','POST'])
@login_required
def take_exam():
 a=db.session.get(Attempt,session.get('attempt_id',0));ids=session.get('question_ids',[])
 if not a or a.user_id!=current_user.id or a.status!='IN_PROGRESS':return redirect(url_for('main.dashboard'))
 if request.method=='POST':
  qid=request.form.get('question_id',type=int); ans=request.form.get('answer'); action=request.form.get('action','next'); ua=UserAnswer.query.filter_by(attempt_id=a.id,question_id=qid).first()
  if ua and ans in {'A','B','C','D'}:ua.selected_answer=ans;db.session.commit()
  i=session.get('current_index',0)
  if action=='prev':i=max(0,i-1)
  elif action=='next':i=min(len(ids)-1,i+1)
  elif action=='goto':i=max(0,min(len(ids)-1,request.form.get('target',0,type=int)))
  elif action=='submit':return redirect(url_for('main.submit_confirm'))
  session['current_index']=i;return redirect(url_for('main.take_exam'))
 i=session.get('current_index',0);q=db.session.get(Question,ids[i]);selected=(UserAnswer.query.filter_by(attempt_id=a.id,question_id=q.id).first() or UserAnswer()).selected_answer
 rem=max(0,int(session.get('deadline',0)-datetime.now(timezone.utc).timestamp()))
 if rem<=0:return redirect(url_for('main.submit_exam'))
 opts=[('A',q.option_a),('B',q.option_b),('C',q.option_c)]+([('D',q.option_d)] if q.option_d else [])
 body=f'<h1>{a.exam.name}</h1><p>Question {i+1} of {len(ids)} | Time remaining: {rem//60:02d}:{rem%60:02d}</p><div class="card"><h2>{q.number}. {q.text}</h2><form method="post">'+''.join(f'<label><input type="radio" name="answer" value="{k}" {"checked" if selected==k else ""}> {k}. {v}</label>' for k,v in opts)+f'<input type="hidden" name="question_id" value="{q.id}"><button name="action" value="prev">Previous</button><button name="action" value="next">Next</button><button name="action" value="submit">Submit Exam</button></form></div>'
 body+='<div>'+''.join(f'<form style="display:inline" method="post"><input type="hidden" name="question_id" value="{q.id}"><input type="hidden" name="action" value="goto"><input type="hidden" name="target" value="{j}"><button>{j+1}</button></form>' for j in range(len(ids)))+'</div>'
 return page(body)
@main_bp.route('/exam/submit-confirm')
@login_required
def submit_confirm():return page('<h1>Submit examination?</h1><form action="/exam/submit"><button>Yes, Submit</button></form><a href="/exam/take">Return to exam</a>')
@main_bp.route('/exam/submit')
@login_required
def submit_exam():
 a=db.session.get(Attempt,session.get('attempt_id',0))
 if not a:return redirect(url_for('main.dashboard'))
 score=sum(1 for x in a.answers if x.selected_answer and x.selected_answer==x.question.correct_answer);a.score=score;a.total=len(a.answers);a.percentage=round(score/a.total*100,2) if a.total else 0;a.submitted_at=datetime.utcnow();a.status='SUBMITTED';db.session.commit();session.clear();return redirect(url_for('main.result',attempt_id=a.id))
@main_bp.route('/result/<int:attempt_id>')
@login_required
def result(attempt_id):
 a=db.session.get(Attempt,attempt_id)
 if not a or a.user_id!=current_user.id:abort(403)
 return page(f'<h1>Exam Result</h1><div class="card"><h2>{a.exam.name}</h2><p>Score: {a.score}/{a.total}</p><p>Percentage: {a.percentage}%</p><p>{"PASS" if a.percentage>=a.exam.pass_mark else "FAIL"}</p></div><a href="/dashboard">Dashboard</a>')
@main_bp.route('/history')
@login_required
def history():
 rows=Attempt.query.filter_by(user_id=current_user.id,status='SUBMITTED').order_by(Attempt.submitted_at.desc()).all();return page('<h1>Exam History</h1>'+''.join(f'<div class="card">{a.exam.name} — {a.percentage}% — {a.submitted_at}</div>' for a in rows))
