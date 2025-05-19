from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import smtplib
from email.message import EmailMessage
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.utils import secure_filename
#from models import db, Student

app = Flask(__name__)
app.secret_key = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
db = SQLAlchemy(app)

EMAIL_ADDRESS = 'philasandemercy.charles@gmail.com'
EMAIL_PASSWORD = 'wfsx adps fpgv styc'

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    student_number = db.Column(db.String(20), unique=True, nullable=False)
    course = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    
@app.route('/')
def index():
    #return render_template('home.html')
    return render_template('index.html', current_page='home')

@app.route('/about')
def about():
    #return render_template('about.html')
    return render_template('about.html', current_page='about')

@app.route('/courses')
def courses():
    #return render_template('courses.html')
    return render_template('courses.html', current_page='courses')

@app.route('/courses/<course_name>')
def course_detail(course_name):
    if 'user_id' not in session:
        return redirect(url_for('lab_layout'))

    template_path = f'templates/{course_name}.html'
    if not os.path.exists(template_path):
        return "Course not found", 404

    return render_template(f'{course_name}.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        msg = EmailMessage()
        msg['Subject'] = 'New Contact Message from Optimus Robotics Lab'
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = EMAIL_ADDRESS
        msg.set_content(f"Name: {name}\nEmail: {email}\nMessage:\n{message}")

        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                smtp.send_message(msg)
            flash('Thanks for reaching out! We will get back to you soon.', 'success')
        except Exception as e:
            flash('Error sending message. Please try again later.', 'danger')

    #return render_template('contact.html')
    return render_template('contact.html', current_page='contact')

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fullname = request.form["fullname"]
        student_number = request.form["student_number"]
        email = request.form["email"]
        course = request.form["course"]
        password = generate_password_hash(request.form["password"])

        if Student.query.filter_by(email=email).first() or Student.query.filter_by(student_number=student_number).first():
            flash("Email or Student Number already registered.", "danger")
            return redirect(url_for("register"))

        student = Student(
            fullname=fullname,
            student_number=student_number,
            email=email,
            course=course,
            password=password,
        )
        db.session.add(student)
        db.session.commit()
        flash("Student registered successfully!", "success")
        return redirect(url_for("login"))
    
    #return render_template("register.html")
    return render_template("register.html", current_page='register')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Try student number first
        user = Student.query.filter((Student.student_number == username) | (Student.email == username)).first()

        if user and check_password_hash(user.password, password):
            session['student_id'] = user.id
            flash('Login successful.', 'success')
            ''''if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:'''
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials.', 'danger')

    #return render_template('login.html')
    return render_template('login.html', current_page='login')

@app.route('/dashboard')
def dashboard():
    if 'student_id' not in session:
        flash('Please log in to access the dashboard.', 'warning')
        return redirect(url_for('login'))
    student = Student.query.get(session['student_id'])
    return render_template('dashboard.html', student=student)

@app.route('/logout')
def logout():
    session.clear()
    #flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/admin')
def admin():
    if 'user' not in session:
        flash("Please login first.", "danger")
        return redirect(url_for('login'))
    return render_template('admin.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'student_id' not in session:
        flash('Login required.', 'warning')
        return redirect(url_for('login'))
    student = Student.query.get(session['student_id'])
    if request.method == 'POST':
        student.fullname = request.form['fullname']
        student.course = request.form['course']
        file = request.files.get('resume')
        if file and file.filename:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            student.resume = filename
        db.session.commit()
        flash('Profile updated.', 'success')
    #return render_template('profile.html', student=student)
    return render_template('profile.html', student=student, current_page='profile')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']
        student = Student.query.filter_by(email=email).first()
        if student:
            new_pw = generate_password_hash('Temp1234', method='sha256')
            student.password = new_pw
            db.session.commit()
            flash('Password reset. Temporary password is: Temp1234', 'info')
        else:
            flash('Email not found.', 'danger')
    return render_template('reset_password.html')

@app.route("/register/admin", methods=["GET", "POST"])
def register_admin():
    if request.method == "POST":
        fullname = request.form["fullname"]
        email = request.form["email"]
        student_number = request.form["student_number"]
        course = request.form["course"]
        password = generate_password_hash(request.form["password"])
        secret_code = request.form["secret_code"]

        if secret_code != "234567":
            flash("Invalid secret code.", "danger")
            return redirect(url_for("register_admin"))

        if Student.query.filter_by(email=email).first() or Student.query.filter_by(student_number=student_number).first():
            flash("Email or Student Number already registered.", "danger")
            return redirect(url_for("register_admin"))

        admin = Student(
            fullname=fullname,
            student_number=student_number,
            email=email,
            course=course,
            password=password,
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        flash("Admin registered successfully!", "success")
        return redirect(url_for("login"))
    
    return render_template("register_admin.html")

@app.route('/poster')
def poster():
    return render_template('poster.html', current_page='poster')

@app.route('/syllabus')
def syllabus():
    return render_template('syllabus.html', current_page='syllabus')

@app.route('/lab-layout')
def lab_layout():
    return render_template('lab_layout.html', current_page='lab_layout')

@app.route('/intro_robot')
def intro_rob():
    return render_template('intro_to_robotics.html', current_page='lab_layout')

@app.route('/machanics')
def machanics():
    return render_template('intro_to_robotics2.html', current_page='lab_layout')

@app.route('/arduino')
def arduino():
    return render_template('arduino.html', current_page='lab_layout')

@app.route('/rasp')
def rasp():
    return render_template('rasp.html', current_page='lab_layout')

@app.route('/electronics')
def electronics():
    return render_template('electronics.html', current_page='lab_layout')

@app.route('/sensors')
def sensors():
    return render_template('sensors.html', current_page='lab_layout')

@app.route('/motion')
def motion():
    return render_template('motion.html', current_page='lab_layout')

@app.route('/cvesion')
def cvesion():
    return render_template('cvesion.html', current_page='lab_layout')

@app.route('/machinelearn')
def machinelearn():
    return render_template('machinelearn.html', current_page='lab_layout')

@app.route('/ros')
def ros():
    return render_template('ros.html', current_page='lab_layout')

@app.route('/robotarm')
def robotarm():
    return render_template('robotarm.html', current_page='lab_layout')

@app.route('/industrial')
def industrial():
    return render_template('industrial.html', current_page='lab_layout')

@app.route('/embeded')
def embeded():
    return render_template('embeded.html', current_page='lab_layout')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)