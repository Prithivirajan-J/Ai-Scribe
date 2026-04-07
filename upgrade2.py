from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
import whisper
import os
import json
import time
import base64
import cv2
import numpy as np
from deepface import DeepFace  # ✅ for face recognition
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-change-me'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///exam.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    reg_no = db.Column(db.String(50), unique=True, nullable=False)
    face_image = db.Column(db.String(200), nullable=False)  # path to stored image

    submissions = db.relationship('Submission', backref='student', lazy=True)


class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    mcq_answers = db.Column(db.Text)  # JSON string
    qa_answers = db.Column(db.Text)   # JSON string


model = whisper.load_model("tiny")

QUESTIONS_FILE = 'questions.json'
SUBMITTED_FILE = 'submitted.json'
REGISTERED_FACE = 'registered_face.jpg'  # Reference image for verification


def load_questions():
    if not os.path.exists(QUESTIONS_FILE):
        return {"mcq": [], "qa": []}

    with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    for qtype in ["mcq", "qa"]:
        if qtype not in data:
            data[qtype] = []
        for q in data[qtype]:
            if "answer" not in q:
                q["answer"] = ""
    return data


def reset_all_answers():
    if os.path.exists(QUESTIONS_FILE):
        with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
            questions = json.load(f)
        for section in ['mcq', 'qa']:
            for item in questions.get(section, []):
                item['answer'] = ""
        with open(QUESTIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(questions, f, indent=2)

    if os.path.exists(SUBMITTED_FILE):
        os.remove(SUBMITTED_FILE)


@app.route('/')
def role_select():
    # New landing page with "Student" / "Teacher" options
    return render_template('role_select.html')


@app.route('/exam')
def exam():
    # Existing student exam interface (face + voice)
    return render_template('upgrade2.html')




@app.route('/questions')
def get_questions():
    return jsonify(load_questions())


@app.route('/save_answer', methods=['POST'])
def save_answer():
    data = request.json
    questions = load_questions()
    if data['type'] == 'mcq':
        for q in questions['mcq']:
            if q['id'] == data['id']:
                q['answer'] = data['answer']
    elif data['type'] == 'qa':
        for q in questions['qa']:
            if q['id'] == data['id']:
                q['answer'] = data['answer']
    with open(QUESTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(questions, f, indent=2)
    return jsonify({'status': 'success'})


@app.route('/transcribe', methods=['POST'])
def transcribe():
    audio_file = request.files['audio']
    if not os.path.exists('transcripts'):
        os.makedirs('transcripts')
    path = os.path.join('transcripts', audio_file.filename)
    audio_file.save(path)
    result = model.transcribe(path, fp16=False, language='en')
    os.remove(path)
    return jsonify({'transcription': result['text'].strip()})


@app.route('/submit', methods=['POST'])
def submit_exam():
    # read current answers from questions.json
    with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
        q = json.load(f)

    # count answered for the small submitted.json summary
    submitted_summary = {
        "time": time.time(),
        "mcq_saved": sum(1 for it in q.get('mcq', []) if it.get('answer')),
        "qa_saved": sum(1 for it in q.get('qa', []) if it.get('answer'))
    }

    # write submitted.json (for your existing functionality)
    with open(SUBMITTED_FILE, 'w', encoding='utf-8') as f:
        json.dump(submitted_summary, f, indent=2)

    # ---- NEW: save into database ----
    student_id = session.get('student_id')  # might be None if not verified
    mcq_answers = json.dumps(q.get('mcq', []), ensure_ascii=False)
    qa_answers = json.dumps(q.get('qa', []), ensure_ascii=False)

    new_sub = Submission(
        student_id=student_id,
        mcq_answers=mcq_answers,
        qa_answers=qa_answers
    )
    db.session.add(new_sub)
    db.session.commit()

    # Reset answers in questions.json so next student starts clean
    for section in ['mcq', 'qa']:
        for item in q.get(section, []):
            item['answer'] = ""
    with open(QUESTIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(q, f, indent=2)

    return jsonify({"status": "ok"})


@app.route('/verify_face', methods=['POST'])
def verify_face():
    try:
        data = request.json
        img_data = data['image'].split(',')[1]
        img_bytes = base64.b64decode(img_data)
        np_img = np.frombuffer(img_bytes, np.uint8)
        captured = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

        students = Student.query.all()
        if not students:
            return jsonify({"verified": False, "message": "No students registered in system."})

        for s in students:
            try:
                result = DeepFace.verify(
                    captured,
                    s.face_image,
                    enforce_detection=False
                )

                if result.get("verified"):
                    session["student_id"] = s.id

                    return jsonify({
                        "verified": True,
                        "name": s.name,
                        "reg_no": s.reg_no,
                        "message": "Face verified successfully!"
                    })

            except Exception as e:
                print("DeepFace inner error:", e)
                continue

        return jsonify({
            "verified": False,
            "message": "Face did not match any registered student."
        })

    except Exception as e:
        return jsonify({
            "verified": False,
            "message": str(e)
        })



@app.route('/faces/<path:filename>')
def serve_face(filename):
    faces_dir = os.path.join(app.root_path, 'faces')
    return send_from_directory(faces_dir, filename)

    
# ------------------ ADMIN AUTH ------------------ #

ADMIN_USERNAME = "teacher"
ADMIN_PASSWORD = "Admin@2004"   # change to whatever you want

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        u = request.form.get('username')
        p = request.form.get('password')
        if u == ADMIN_USERNAME and p == ADMIN_PASSWORD:
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error="Invalid credentials")
    return render_template('admin_login.html', error=None)


@app.route('/admin/logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect(url_for('admin_login'))


def admin_required(func):
    """Simple decorator to protect admin routes."""
    from functools import wraps
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('admin_login'))
        return func(*args, **kwargs)
    return wrapper

# ------------------ ADMIN PAGES ------------------ #

@app.route('/admin')
@admin_required
def admin_dashboard():
    students = Student.query.order_by(Student.id).all()
    return render_template('admin_dashboard.html', students=students)


@app.route('/admin/students/add', methods=['GET', 'POST'])
@admin_required
def admin_add_student():
    if request.method == 'POST':
        name = request.form.get('name')
        reg_no = request.form.get('reg_no')
        file = request.files.get('face_image')

        if not (name and reg_no and file):
            return "Missing fields", 400

        # ✅ Save image inside static/faces
        faces_dir = os.path.join(app.root_path, 'faces')
        os.makedirs(faces_dir, exist_ok=True)
        filename = f"{reg_no}.jpg"
        save_path = os.path.join(faces_dir, filename)
        file.save(save_path)

        student = Student(name=name, reg_no=reg_no, face_image=save_path)

        db.session.add(student)
        db.session.commit()

        print("✅ Saved student:", name, reg_no, "image at", save_path)

        return redirect(url_for('admin_dashboard'))

    # GET: render form
    return render_template('admin_add_student.html')


@app.route('/admin/submissions')
@admin_required
def admin_submissions():
    subs = Submission.query.order_by(Submission.timestamp.desc()).all()
    return render_template('admin_submissions.html', submissions=subs)

@app.route('/admin/submissions/<int:submission_id>')
@admin_required
def admin_view_submission(submission_id):
    sub = Submission.query.get_or_404(submission_id)
    mcq = json.loads(sub.mcq_answers or "[]")
    qa = json.loads(sub.qa_answers or "[]")
    return render_template('admin_view_submission.html',
                           sub=sub, mcq=mcq, qa=qa)


if __name__ == '__main__':
    reset_all_answers()
    with app.app_context():
        db.create_all()
    app.run(debug=True)

