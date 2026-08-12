import csv,io
from flask import Blueprint,request,redirect,url_for,flash,render_template_string,abort
from flask_login import login_required,current_user
from . import db
from .models import Question,Exam
admin_bp=Blueprint('admin',__name__,url_prefix='/admin')
def req():
 if not current_user.is_authenticated or not current_user.is_admin:abort(403)
@admin_bp.route('/questions')
@login_required
def questions():
 req(); qs=Question.query.order_by(Question.exam_id,Question.number).all();return render_template_string('<h1>Questions</h1><a href="/admin/import">Import CSV/TXT</a><ul>{% for q in qs %}<li>{{q.number}}. {{q.text}} — {{q.correct_answer}}</li>{% endfor %}</ul>',qs=qs)
@admin_bp.route('/import',methods=['GET','POST'])
@login_required
def import_questions():
 req(); exams=Exam.query.all()
 if request.method=='POST':
  exam_id=request.form.get('exam_id',type=int); f=request.files.get('file')
  if not exam_id or not f:flash('Select an exam and file.');return redirect(request.url)
  reader=csv.DictReader(io.StringIO(f.read().decode('utf-8-sig',errors='replace')));n=0
  for i,row in enumerate(reader,1):
   if not row.get('question'):continue
   db.session.add(Question(exam_id=exam_id,number=int(row.get('number') or i),text=row['question'],option_a=row.get('A') or row.get('option_a',''),option_b=row.get('B') or row.get('option_b',''),option_c=row.get('C') or row.get('option_c',''),option_d=row.get('D') or row.get('option_d') or None,correct_answer=(row.get('correct_answer') or '').upper() or None,explanation=row.get('explanation',''),difficulty=row.get('difficulty','Medium')));n+=1
  db.session.commit();flash(f'Imported {n} questions.');return redirect(url_for('admin.questions'))
 return render_template_string('<h1>Import questions</h1><form method="post" enctype="multipart/form-data"><select name="exam_id">{% for e in exams %}<option value="{{e.id}}">{{e.name}}</option>{% endfor %}</select><input type="file" name="file" accept=".csv"><button>Import</button></form>',exams=exams)
