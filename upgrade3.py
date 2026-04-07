from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
import os
import json
import time
import base64
import cv2
import numpy as np
from deepface import DeepFace
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-change-me'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///exam.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ================= DATABASE MODELS =================

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    reg_no = db.Column(db.String(50), unique=True, nullable=False)
    face_image = db.Column(db.String(200), nullable=False)

class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    mcq_answers = db.Column(db.Text)
    qa_answers = db.Column(db.Text)

# ================= FILE CONFIG =================

QUESTIONS_FILE = 'questions.json'
SUBMITTED_FILE = 'submitted.json'

# ================= ROUTES =================

@app.route('/')
def role_select():
    return render_template('role_select.html')

@app.route('/exam')
def exam():
    return render_template('upgrade3.html')

# ================= QUESTIONS =================

def load_questions():
    if not os.path.exists(QUESTIONS_FILE):
        return {"mcq": [], "qa": []}

    with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for section in ["mcq", "qa"]:
        for q in data.get(section, []):
            q.setdefault("answer", "")

    return data

@app.route('/questions')
def get_questions():
    return jsonify(load_questions())

@app.route('/save_answer', methods=['POST'])
def save_answer():
    data = request.json
    questions = load_questions()

    for q in questions[data['type']]:
        if q['id'] == data['id']:
            q['answer'] = data['answer']

    with open(QUESTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(questions, f, indent=2)

    return jsonify({'status': 'success'})

# ================= SUBMIT =================

@app.route('/submit', methods=['POST'])
def submit_exam():
    with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
        q = json.load(f)

    summary = {
        "time": time.time(),
        "mcq_saved": sum(1 for it in q.get('mcq', []) if it.get('answer'))
    }

    with open(SUBMITTED_FILE, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    student_id = session.get('student_id')

    new_sub = Submission(
        student_id=student_id,
        mcq_answers=json.dumps(q.get('mcq', []))
    )

    db.session.add(new_sub)
    db.session.commit()

    # reset answers
    for it in q.get('mcq', []):
        it['answer'] = ""

    with open(QUESTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(q, f, indent=2)

    return jsonify({"status": "ok"})

# ================= FACE VERIFICATION =================

@app.route('/verify_face', methods=['POST'])
def verify_face():
    data = request.json
    img_data = data['image'].split(',')[1]
    img_bytes = base64.b64decode(img_data)
    np_img = np.frombuffer(img_bytes, np.uint8)
    captured = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    students = Student.query.all()

    for s in students:
        result = DeepFace.verify(captured, s.face_image, enforce_detection=False)
        if result.get("verified"):
            session["student_id"] = s.id
            return jsonify({
                "verified": True,
                "name": s.name,
                "reg_no": s.reg_no
            })

    return jsonify({"verified": False})

# ================= ADMIN (UNCHANGED) =================

ADMIN_USERNAME = "teacher"
ADMIN_PASSWORD = "secret123"

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USERNAME and request.form['password'] == ADMIN_PASSWORD:
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')

@app.route('/admin')
def admin_dashboard():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    students = Student.query.all()
    return render_template('admin_dashboard.html', students=students)

# ================= MAIN =================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)