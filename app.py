import os
import json
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from streamlit import video
from werkzeug.utils import secure_filename
from youtube_uploader import (upload_video_to_youtube, get_authenticated_service, create_playlist_if_missing,)
from config import CLASSROOM_OWNER_EMAIL
from classroom_utils import create_google_course
from classroom_auth import get_classroom_service
import uuid
from datetime import datetime, timedelta
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from pytz import timezone as ZoneInfo
import re

from flask_login import UserMixin


from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import current_user

#CLASSES_FILE = "data/classes.json"
#VIDEOS_FILE = "data/videos.json"

basedir = os.path.abspath(os.path.dirname(__file__))


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "fallback_dev_secret")
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'data', 'SciMindMain.db')}")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

creds = os.environ.get("GOOGLE_CREDENTIALS_JSON")
if creds:
    os.makedirs("config", exist_ok=True)
    with open("config/webportal_credentials.json", "w") as f:
        f.write(creds)
 
migrate = Migrate(app, db)

# Ensure current_user is available in all templates
@app.context_processor
def inject_user():
    from flask_login import current_user
    return dict(current_user=current_user)



# === Updated Models from DBML ===
class UserAccount(UserMixin, db.Model):
    __tablename__ = 'user_account'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    role = db.Column(db.String)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    google_email = db.Column(db.String)
    profile_picture_url = db.Column(db.Text)
    # Relationships
    classes_taught = db.relationship('Class', foreign_keys='Class.class_teacher', backref='teacher', lazy='dynamic')
    classes_updated = db.relationship('Class', foreign_keys='Class.updated_by', backref='class_updated_by', lazy='dynamic')
    videos_uploaded = db.relationship('Video', foreign_keys='Video.uploaded_by', backref='uploader', lazy='dynamic')
    student_fees_updated = db.relationship('StudentFee', foreign_keys='StudentFee.updated_by', backref='fee_updated_by', lazy='dynamic')
    attendances_updated = db.relationship('Attendance', foreign_keys='Attendance.updated_by', backref='attendance_updated_by', lazy='dynamic')
    payments_updated = db.relationship('Payment', foreign_keys='Payment.updated_by', backref='payment_updated_by', lazy='dynamic')
    google_accounts_owned = db.relationship('GoogleIntegrationAccount', foreign_keys='GoogleIntegrationAccount.owner_user_id', backref='owner', lazy='dynamic')
    google_courses_created = db.relationship('GoogleClassroomCourse', foreign_keys='GoogleClassroomCourse.created_by', backref='course_creator', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Class(db.Model):
    __tablename__ = 'class'
    id = db.Column(db.Integer, primary_key=True)
    class_code = db.Column(db.String, unique=True, nullable=False)
    class_status = db.Column(db.String)
    class_name = db.Column(db.String)
    subject = db.Column(db.String)
    year_level = db.Column(db.String)
    batch = db.Column(db.String)
    sub_batch = db.Column(db.String)
    class_type = db.Column(db.String)
    description = db.Column(db.String)
    playlist_id = db.Column(db.String)
    class_created = db.Column(db.DateTime)
    class_teacher = db.Column(db.Integer, db.ForeignKey('user_account.id'))
    class_day = db.Column(db.String)
    class_time = db.Column(db.String)
    class_location = db.Column(db.String)
    updated_by = db.Column(db.Integer, db.ForeignKey('user_account.id'))
    updated_at = db.Column(db.DateTime)
    # Relationships
    videos = db.relationship('Video', backref='class_', lazy='dynamic')
    assignments = db.relationship('StudentClassAssignment', backref='class_', lazy='dynamic')
    fees = db.relationship('StudentFee', backref='class_', lazy='dynamic')
    attendances = db.relationship('Attendance', backref='class_', lazy='dynamic')
    google_courses = db.relationship('GoogleClassroomCourse', backref='class_', lazy='dynamic')

class Video(db.Model):
    __tablename__ = 'video'
    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.String, unique=True, nullable=False)
    title = db.Column(db.String)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'))
    youtube_playlist_id = db.Column(db.String)
    classroom_posted = db.Column(db.Boolean)
    integration_account_id = db.Column(db.Integer, db.ForeignKey('google_integration_account.id'), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user_account.id'))
    published_at = db.Column(db.DateTime)

class Student(db.Model):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key=True)
    student_code = db.Column(db.String, unique=True, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    last_name = db.Column(db.String, nullable=False)
    dob = db.Column(db.Date)
    gender = db.Column(db.String)
    contact_number = db.Column(db.String)
    grade_school = db.Column(db.String)
    student_email = db.Column(db.String)
    address = db.Column(db.String)
    notes = db.Column(db.Text)
    status = db.Column(db.String)
    created_at = db.Column(db.DateTime)
    updated_by = db.Column(db.Integer, db.ForeignKey('user_account.id'))
    updated_at = db.Column(db.DateTime)
    # Relationships
    parents = db.relationship('Parent', backref='student', lazy='dynamic')
    assignments = db.relationship('StudentClassAssignment', backref='student', lazy='dynamic')
    fees = db.relationship('StudentFee', backref='student', lazy='dynamic')
    attendances = db.relationship('Attendance', backref='student', lazy='dynamic')
    payments = db.relationship('Payment', backref='student', lazy='dynamic')

class Parent(db.Model):
    __tablename__ = 'parent'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    name = db.Column(db.String, nullable=False)
    relationship = db.Column(db.String)
    contact_number = db.Column(db.String)
    parent_email = db.Column(db.String)

class StudentClassAssignment(db.Model):
    __tablename__ = 'student_class_assignment'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'))
    enrolled_from = db.Column(db.Date)
    enrolled_to = db.Column(db.Date)
    is_primary = db.Column(db.Boolean)

class StudentFee(db.Model):
    __tablename__ = 'student_fee'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'))
    fee_type = db.Column(db.String)
    amount_due = db.Column(db.Float)
    amount_paid = db.Column(db.Float)
    discount = db.Column(db.Float)
    due_date = db.Column(db.Date)
    payment_status = db.Column(db.String)
    notes = db.Column(db.Text)
    updated_by = db.Column(db.Integer, db.ForeignKey('user_account.id'))
    updated_at = db.Column(db.DateTime)

class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'))
    date = db.Column(db.Date)
    status = db.Column(db.String)
    notes = db.Column(db.Text)
    updated_by = db.Column(db.Integer, db.ForeignKey('user_account.id'))
    updated_at = db.Column(db.DateTime)

class Payment(db.Model):
    __tablename__ = 'payment'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    fee_id = db.Column(db.Integer, db.ForeignKey('student_fee.id'))
    amount = db.Column(db.Float)
    date = db.Column(db.DateTime)
    method = db.Column(db.String)
    reference = db.Column(db.String)
    notes = db.Column(db.Text)
    updated_by = db.Column(db.Integer, db.ForeignKey('user_account.id'))
    updated_at = db.Column(db.DateTime)

class GoogleIntegrationAccount(db.Model):
    __tablename__ = 'google_integration_account'
    id = db.Column(db.Integer, primary_key=True)
    account_name = db.Column(db.String)
    google_email = db.Column(db.String, unique=True, nullable=False)
    access_token = db.Column(db.Text)
    refresh_token = db.Column(db.Text)
    owner_user_id = db.Column(db.Integer, db.ForeignKey('user_account.id'), nullable=False)
    created_at = db.Column(db.DateTime)
    last_synced = db.Column(db.DateTime)
    # Relationships
    videos = db.relationship('Video', backref='integration_account', lazy='dynamic')
    permissions = db.relationship('GoogleAccountPermissions', backref='integration_account', lazy='dynamic')
    classroom_courses = db.relationship('GoogleClassroomCourse', backref='integration_account', lazy='dynamic')

class GoogleAccountPermissions(db.Model):
    __tablename__ = 'google_account_permissions'
    id = db.Column(db.Integer, primary_key=True)
    integration_account_id = db.Column(db.Integer, db.ForeignKey('google_integration_account.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user_account.id'), nullable=False)
    permission_level = db.Column(db.String)

class GoogleClassroomCourse(db.Model):
    __tablename__ = 'google_classroom_course'
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.String, unique=True, nullable=False)
    name = db.Column(db.String)
    section = db.Column(db.String)
    join_code = db.Column(db.String)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'))
    integration_account_id = db.Column(db.Integer, db.ForeignKey('google_integration_account.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user_account.id'))
    created_at = db.Column(db.DateTime)

# --- User Management Routes ---
@app.route('/users')
def users():
    user_list = UserAccount.query.all()
    accounts = GoogleIntegrationAccount.query.all()
    return render_template('manage_users.html', users=user_list, google_accounts=accounts)

@app.route('/add_user', methods=['POST'])
def add_user():
    data = request.form
    user = UserAccount(
        username=data['username'],
        email=data['email'],
        role=data.get('role', 'user'),
        active=True
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    flash('User added successfully!', 'success')
    return redirect(url_for('users'))

@app.route('/edit_user/<int:id>', methods=['POST'])
def edit_user(id):
    user = UserAccount.query.get_or_404(id)
    data = request.form
    user.username = data['username']
    user.email = data['email']
    user.role = data.get('role', user.role)
    user.active = 'active' in data
    db.session.commit()
    flash('User updated successfully!', 'success')
    return redirect(url_for('users'))

@app.route('/delete_user/<int:id>', methods=['POST'])
def delete_user(id):
    user = UserAccount.query.get_or_404(id)
    user.active = False
    db.session.commit()
    flash('User deactivated.', 'info')
    return redirect(url_for('users'))

# Deactivate User Route
@app.route('/deactivate_user/<int:id>', methods=['POST'])
def deactivate_user(id):
    user = UserAccount.query.get_or_404(id)
    user.active = False
    db.session.commit()
    flash('User deactivated.', 'info')
    return redirect(url_for('users'))

@app.route('/change_password/<int:id>', methods=['POST'])
def change_password(id):
    user = UserAccount.query.get_or_404(id)
    data = request.form
    new_password = data['new_password']
    user.set_password(new_password)
    db.session.commit()
    flash('Password changed successfully!', 'success')
    return redirect(url_for('users'))

# === Login Setup ===
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

# === Dummy User Class ===


@login_manager.user_loader
def load_user(user_id):
    return UserAccount.query.get(int(user_id))

# === Routes ===

@app.errorhandler(401)
def unauthorized(e):
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    return redirect(url_for("login"))

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        try:
            username = request.form.get("username")
            password = request.form.get("password")
            user = UserAccount.query.filter_by(username=username).first()
            # Defensive checks for user existence, active status, and password hash
            if user is not None and user.active and hasattr(user, 'password_hash') and user.password_hash:
                if user.check_password(password):
                    login_user(user)
                    return redirect(url_for("dashboard"))
                else:
                    error = "Invalid username or password"
            else:
                error = "Invalid username or password"
        except Exception as e:
            print(f"[LOGIN ERROR] {e}")
            error = "An unexpected error occurred. Please try again."
    return render_template("login.html", error=error)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/upload")
@login_required
def upload():
    # Fetch all classes from the database
    class_objs = Class.query.all()
    classes = {}
    for c in class_objs:
        # Fetch the latest GoogleClassroomCourse for this class (if any)
        gclass = (
            GoogleClassroomCourse.query.filter_by(class_id=c.id)
            .order_by(GoogleClassroomCourse.created_at.desc())
            .first()
        )
        classes[c.class_code] = {
            "class_name": c.class_name,
            "subject": c.subject,
            "year_level": c.year_level,
            "batch": c.batch,
            "sub_batch": c.sub_batch,
            "class_type": c.class_type,
            "description": c.description,
            "playlist_id": c.playlist_id,
            "courseId": gclass.course_id if gclass else None,
            "joinCode": gclass.join_code if gclass else None,
            "classroom_name": gclass.name if gclass else None,
            "classroom_section": gclass.section if gclass else None,
            "last_updated": c.last_updated.isoformat() if getattr(c, 'last_updated', None) else None,
            "class_created": c.class_created.isoformat() if c.class_created else None,
            "class_teacher": c.class_teacher,
            "class_day": c.class_day,
            "class_time": c.class_time,
            "class_location": c.class_location,
            "class_status": c.class_status
        }
    return render_template("upload.html", classes=classes)

# === Google Integration Account & Permissions Management (Admin Only) ===
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or getattr(current_user, 'role', None) != 'admin':
            return jsonify({"status": "error", "message": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated_function

# --- GoogleIntegrationAccount CRUD ---
@app.route('/api/google_accounts', methods=['GET'])
@login_required
@admin_required
def list_google_accounts():
    accounts = GoogleIntegrationAccount.query.all()
    return jsonify([
        {
            'id': acc.id,
            'account_name': acc.account_name,
            'google_email': acc.google_email,
            'owner_user_id': acc.owner_user_id,
            'created_at': acc.created_at.isoformat() if acc.created_at else None,
            'last_synced': acc.last_synced.isoformat() if acc.last_synced else None
        } for acc in accounts
    ])

@app.route('/api/google_accounts', methods=['POST'])
@login_required
@admin_required
def add_google_account():
    data = request.json
    acc = GoogleIntegrationAccount(
        account_name=data.get('account_name'),
        google_email=data['google_email'],
        access_token=data.get('access_token'),
        refresh_token=data.get('refresh_token'),
        owner_user_id=data['owner_user_id'],
        created_at=datetime.utcnow()
    )
    db.session.add(acc)
    db.session.commit()
    return jsonify({'id': acc.id}), 201

@app.route('/api/google_accounts/<int:acc_id>', methods=['PUT'])
@login_required
@admin_required
def edit_google_account(acc_id):
    acc = GoogleIntegrationAccount.query.get_or_404(acc_id)
    data = request.json
    for field in ['account_name', 'google_email', 'access_token', 'refresh_token', 'owner_user_id']:
        if field in data:
            setattr(acc, field, data[field])
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/api/google_accounts/<int:acc_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_google_account(acc_id):
    acc = GoogleIntegrationAccount.query.get_or_404(acc_id)
    db.session.delete(acc)
    db.session.commit()
    return jsonify({'status': 'deleted'})

# --- GoogleAccountPermissions CRUD ---
@app.route('/api/google_permissions', methods=['GET'])
@login_required
@admin_required
def list_google_permissions():
    perms = GoogleAccountPermissions.query.all()
    return jsonify([
        {
            'id': p.id,
            'integration_account_id': p.integration_account_id,
            'user_id': p.user_id,
            'permission_level': p.permission_level
        } for p in perms
    ])

@app.route('/api/google_permissions', methods=['POST'])
@login_required
@admin_required
def add_google_permission():
    data = request.json
    perm = GoogleAccountPermissions(
        integration_account_id=data['integration_account_id'],
        user_id=data['user_id'],
        permission_level=data.get('permission_level', 'uploader')
    )
    db.session.add(perm)
    db.session.commit()
    return jsonify({'id': perm.id}), 201

@app.route('/api/google_permissions/<int:perm_id>', methods=['PUT'])
@login_required
@admin_required
def edit_google_permission(perm_id):
    perm = GoogleAccountPermissions.query.get_or_404(perm_id)
    data = request.json
    for field in ['integration_account_id', 'user_id', 'permission_level']:
        if field in data:
            setattr(perm, field, data[field])
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/api/google_permissions/<int:perm_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_google_permission(perm_id):
    perm = GoogleAccountPermissions.query.get_or_404(perm_id)
    db.session.delete(perm)
    db.session.commit()
    return jsonify({'status': 'deleted'})

print("🧠 Rendered upload view")



@app.route("/api/upload_video", methods=["POST"])
@login_required
def api_upload_video():
    print("📡 Received upload request")
    try:
        # --- Get form data ---
        file = request.files.get("file")
        class_selected = request.form.get("class_selected")
        class_name = request.form.get("class_name")
        title = request.form.get("title")
        description = request.form.get("description", "")
        post_to_classroom = request.form.get("post_to_classroom") == "true"

        # --- Validate required fields ---
        if not file:
            return jsonify({"status": "error", "message": "No file uploaded."}), 400
        if not class_selected:
            return jsonify({"status": "error", "message": "No class selected."}), 400
        if not title:
            return jsonify({"status": "error", "message": "No title provided."}), 400

        # --- Save file locally ---
        try:
            filename = secure_filename(file.filename)
            upload_dir = "temp_uploads"
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
        except Exception as e:
            print("[UPLOAD ERROR] File save failed:", e)
            return jsonify({"status": "error", "message": f"Failed to save file: {e}"}), 500

        # --- YouTube upload ---
        try:
            youtube = get_authenticated_service()
            playlist_id = create_playlist_if_missing(youtube, class_name or class_selected)
            video_id = upload_video_to_youtube(file_path, title, description, playlist_id)
            video_url = f"https://www.youtube.com/watch?v={video_id}"
        except Exception as e:
            print("[YOUTUBE ERROR]", e)
            return jsonify({"status": "error", "message": f"YouTube upload failed: {e}"}), 500

        # --- Update class metadata in DB ---
        cls = Class.query.filter_by(class_code=class_selected).first()
        if cls:
            cls.playlist_id = playlist_id
            try:
                melbourne_time = datetime.now(ZoneInfo('Australia/Melbourne'))
            except Exception:
                melbourne_time = datetime.utcnow()
            cls.last_updated = melbourne_time
            db.session.commit()

        # --- Find integration_account_id for current user ---
        from sqlalchemy import and_
        perm = (
            db.session.query(GoogleAccountPermissions)
            .filter(GoogleAccountPermissions.user_id == current_user.id)
            .first()
        )
        if not perm:
            return jsonify({"status": "error", "message": "No Google integration account permission found for user."}), 400
        integration_account_id = perm.integration_account_id

        # --- Build and save video entry ---
        new_video = Video(
            video_id=video_id,
            title=title,
            class_id=cls.id if cls else None,
            youtube_playlist_id=playlist_id,
            classroom_posted=False,
            integration_account_id=integration_account_id,
            uploaded_by=current_user.id,
            published_at=datetime.utcnow()
        )
        db.session.add(new_video)
        db.session.commit()

        # --- Post to Google Classroom as YouTube video attachment if needed ---
        classroom_status = "Not posted to Classroom"
        if post_to_classroom:
            # Fetch GoogleClassroomCourse for this class
            gclass = None
            if cls:
                gclass = (
                    GoogleClassroomCourse.query.filter_by(class_id=cls.id)
                    .order_by(GoogleClassroomCourse.created_at.desc())
                    .first()
                )
            if gclass and gclass.course_id:
                try:
                    service = get_classroom_service()
                    # Extract YouTube video ID from URL
                    video_id_only = video_url.split("v=")[-1]
                    announcement = {
                        "text": description,
                        "materials": [
                            {"youtubeVideo": {"id": video_id_only}}
                        ]
                    }
                    service.courses().announcements().create(courseId=gclass.course_id, body=announcement).execute()
                    new_video.classroom_posted = True
                    classroom_status = "Posted to Google Classroom ✅"
                    db.session.commit()
                except Exception as e:
                    print("[CLASSROOM ERROR]", e)
                    classroom_status = f"Failed to post to Classroom: {e}"
            else:
                classroom_status = "Class not linked to Google Classroom"

        # --- Return response ---
        return jsonify({
            "status": "success",
            "title": title,
            "video_url": video_url,
            "classroom_status": classroom_status
        })

    except Exception as e:
        print("[GENERAL UPLOAD ERROR]", e)
        return jsonify({"status": "error", "message": f"Unexpected error: {e}"}), 500

## Removed duplicate manage_classes function

@app.route("/add_class", methods=["POST"])
@login_required
def add_class():

    subject = request.form["subject"].strip()
    year_level = request.form["year_level"].strip()
    batch = request.form["batch"].strip()
    sub_batch = request.form.get("sub_batch", "").strip()
    class_type = request.form.get("class_type", "").strip()
    description = request.form.get("description", "").strip()
    class_teacher = request.form.get("class_teacher", "Nisa Bandarayapa").strip()
    class_day = request.form.get("class_day", "Monday").strip()
    class_time = request.form.get("class_time", "").strip()
    class_location = request.form.get("class_location", "").strip()

    create_gclassroom = "create_classroom" in request.form
    gclass_name = request.form.get("gclass_name", "").strip()
    gclass_section = request.form.get("gclass_section", "").strip()

    # Build unique class code
    subject_code = subject.replace(" ", "")[:3].upper()
    year_match = re.search(r'\d+', year_level)
    year_code = year_match.group(0) if year_match else ""
    batch_code = batch
    sub_batch_code = sub_batch.replace(" ", "").upper() if sub_batch else ""
    class_type_code = class_type[0].upper() if class_type else ""
    class_code = f"{subject_code}{year_code}{batch_code}{sub_batch_code}{class_type_code}"
    class_name = f"{subject} - {year_level} - {batch}"
    if sub_batch and sub_batch.strip():
        class_name += f" - {sub_batch.strip()}"

    edit_code = request.form.get("edit_code")
    if edit_code:
        cls = Class.query.get(edit_code)
        if not cls:
            flash("⚠️ That class no longer exists.", "warning")
            return redirect(url_for("manage_classes", tab="list"))
        cls.subject = subject
        cls.year_level = year_level
        cls.batch = batch
        cls.sub_batch = sub_batch
        cls.class_type = class_type
        cls.description = description
        cls.class_name = class_name
        cls.class_teacher = class_teacher
        cls.class_day = class_day
        cls.class_time = class_time
        cls.class_location = class_location
        db.session.commit()
        flash(f"🔁 Class '{class_name}' updated successfully.", "success")
    else:
        # Check for duplicates (now includes sub_batch and class_type for uniqueness)
        duplicate = Class.query.filter_by(subject=subject, year_level=year_level, batch=batch, sub_batch=sub_batch, class_type=class_type).first()
        if duplicate:
            flash("⚠️ A class with the same subject, year, batch, sub batch, and type already exists.", "warning")
            return redirect(url_for("manage_classes", tab="add"))

        try:
            melbourne_time = datetime.now(ZoneInfo('Australia/Melbourne'))
        except Exception:
            # Fallback: use UTC and manually add offset for Melbourne (does not handle DST)
            melbourne_time = datetime.utcnow() + timedelta(hours=10)

        new_class = Class(
            class_code=class_code,
            class_name=class_name,
            subject=subject,
            year_level=year_level,
            batch=batch,
            sub_batch=sub_batch,
            class_type=class_type,
            description=description,
            class_status="active",
            class_created=melbourne_time,
            class_teacher=class_teacher,
            class_day=class_day,
            class_time=class_time,
            class_location=class_location
        )

        # ✅ Google Classroom Creation
        if create_gclassroom and gclass_name:
            try:
                course_info = create_google_course(
                    course_name=gclass_name,
                    section=gclass_section,
                    room=batch,
                    ownerId=CLASSROOM_OWNER_EMAIL
                )
                new_class.courseId = course_info["courseId"]
                new_class.joinCode = course_info["joinCode"]
                new_class.classroom_name = gclass_name
                new_class.classroom_section = gclass_section
                db.session.add(new_class)
                db.session.flush()  # Get new_class.id before committing
                # Insert GoogleClassroomCourse record
                integration_account_id = 1  # TODO: Use real integration account selection logic
                created_by = current_user.id if current_user.is_authenticated else None
                gclass = GoogleClassroomCourse(
                    course_id=course_info["courseId"],
                    name=gclass_name,
                    section=gclass_section,
                    join_code=course_info["joinCode"],
                    class_id=new_class.id,
                    integration_account_id=integration_account_id,
                    created_by=created_by,
                    created_at=datetime.utcnow()
                )
                db.session.add(gclass)
                flash(f"✅ Classroom created with join code: {course_info['joinCode']}", "info")
            except Exception as e:
                db.session.add(new_class)
                flash(f"⚠️ Classroom creation failed: {e}", "warning")
        else:
            db.session.add(new_class)
        flash(f"✅ Class '{class_name}' created successfully!", "success")
    db.session.commit()
    return redirect(url_for("manage_classes", tab="list"))

@app.route("/delete_class/<code>", methods=["POST"])
@login_required
def delete_class(code):
    cls = Class.query.filter_by(class_code=code).first()
    if cls:
        # Cascade delete related records
        GoogleClassroomCourse.query.filter_by(class_id=cls.id).delete()
        StudentClassAssignment.query.filter_by(class_id=cls.id).delete()
        Video.query.filter_by(class_id=cls.id).delete()
        StudentFee.query.filter_by(class_id=cls.id).delete()
        Attendance.query.filter_by(class_id=cls.id).delete()
        db.session.delete(cls)
        db.session.commit()
        flash(f"🗑️ Class '{cls.class_name}' and all related records deleted.", "success")
    else:
        flash(f"⚠️ Class '{code}' not found.", "warning")
    return redirect(url_for("manage_classes", tab="list"))

# === AJAX Edit Class Route ===
@app.route("/edit_class/<code>", methods=["POST"])
@login_required
def edit_class(code):
    cls = Class.query.filter_by(class_code=code).first()
    if not cls:
        return jsonify({"status": "error", "message": "Class not found"}), 404
    data = request.get_json()
    # Update fields if present in request
    if "subject" in data:
        cls.subject = data["subject"].strip()
    if "year_level" in data:
        cls.year_level = data["year_level"].strip()
    if "batch" in data:
        cls.batch = data["batch"].strip()
    if "sub_batch" in data:
        cls.sub_batch = data["sub_batch"].strip()
    if "class_type" in data:
        cls.class_type = data["class_type"].strip()
    if "description" in data:
        cls.description = data["description"].strip()
    if "teacher" in data:
        cls.class_teacher = data["teacher"].strip()
    if "class_day" in data:
        cls.class_day = data["class_day"].strip()
    if "class_time" in data:
        cls.class_time = data["class_time"].strip()
    if "class_location" in data:
        cls.class_location = data["class_location"].strip()
    if "active" in data:
        cls.class_status = "active" if data["active"] else "inactive"
    # Update class_name with sub_batch if available
    class_name = f"{cls.subject} - {cls.year_level} - {cls.batch}"
    if cls.sub_batch and cls.sub_batch.strip():
        class_name += f" - {cls.sub_batch.strip()}"
    cls.class_name = class_name
    # Set last_updated to Melbourne time (handles DST)
    try:
        melbourne_time = datetime.now(ZoneInfo('Australia/Melbourne'))
    except Exception:
        melbourne_time = datetime.utcnow()
    cls.last_updated = melbourne_time
    db.session.commit()
    return jsonify({"status": "success", "message": "Class updated"})



# New AJAX-friendly API endpoint for Google Classroom linking
@app.route("/api/link_google_classroom/<code>", methods=["POST"])
@login_required
def api_link_google_classroom(code):
    cls = Class.query.filter_by(class_code=code).first()
    if not cls:
        return jsonify({"status": "error", "message": "Class not found."}), 404
    data = request.get_json()
    gclass_name = (data.get("gclass_name") or "").strip()
    gclass_section = (data.get("gclass_section") or "").strip()
    if not gclass_name:
        return jsonify({"status": "error", "message": "Google Classroom name is required."}), 400
    try:
        course_info = create_google_course(
            course_name=gclass_name,
            section=gclass_section,
            room=cls.batch,
            ownerId=CLASSROOM_OWNER_EMAIL
        )
        # Save to GoogleClassroomCourse table
        integration_account_id = 1  # TODO: Use real integration account selection logic
        created_by = current_user.id if current_user.is_authenticated else None
        gclass = GoogleClassroomCourse(
            course_id=course_info["courseId"],
            name=gclass_name,
            section=gclass_section,
            join_code=course_info["joinCode"],
            class_id=cls.id,
            integration_account_id=integration_account_id,
            created_by=created_by,
            created_at=datetime.utcnow()
        )
        db.session.add(gclass)
        db.session.commit()
        return jsonify({
            "status": "success",
            "message": f"Google Classroom linked successfully! Join code: {gclass.join_code}",
            "join_code": gclass.join_code,
            "course_id": gclass.course_id,
            "classroom_name": gclass.name,
            "classroom_section": gclass.section
        })
    except Exception as e:
        print("Google Classroom Error:", e)
        return jsonify({"status": "error", "message": f"Failed to create Google Classroom: {e}"}), 500

@app.route("/post_video_to_classroom/<video_id>", methods=["POST"])
@login_required
def post_video_to_classroom(video_id):
    try:
        # 📂 Load video from DB
        video = Video.query.get(video_id)
        if not video:
            return jsonify({"status": "error", "message": "Video not found"}), 404

        # 📘 Load class from DB
        cls = Class.query.get(video.class_code)
        course_id = cls.courseId if cls else None

        if not course_id:
            return jsonify({"status": "error", "message": "Class not linked to Classroom"}), 400

        # 📢 Post to Classroom stream
        service = get_classroom_service()
        video_url = f"https://www.youtube.com/watch?v={video.youtube_id}"
        announcement = {
            "text": f"📽️ Video: *{video.title}*\nWatch: {video_url}"
        }

        service.courses().announcements().create(courseId=course_id, body=announcement).execute()

        # ✅ Update post status
        video.classroom_posted = True
        db.session.commit()
        print("✅ Updating classroom_posted for:", video.id)

        return jsonify({"status": "success", "message": "Posted to Classroom successfully."})
    except Exception as e:
        print("Classroom post error:", e)
        return jsonify({"status": "error", "message": str(e)}), 500
# === STUDENT API ENDPOINTS ===


@app.route('/manage_students')
@login_required
def manage_students():
    # Fetch all students
    students = Student.query.all()
    # Fetch all classes for dropdowns
    classes = Class.query.all()
    # Build student data with class assignments
    student_list = []
    for s in students:
        # Get all assignments for this student
        assignments = StudentClassAssignment.query.filter_by(student_id=s.id).all()
        class_assignments = []
        for a in assignments:
            class_obj = Class.query.get(a.class_id)
            class_name = class_obj.class_name if class_obj else "Unknown"
            enrolled_date = a.enrolled_from.isoformat() if a.enrolled_from else ""
            class_assignments.append({
                "class_name": class_name,
                "enrolled_date": enrolled_date
            })
        student_list.append({
            "id": s.id,
            "student_id": s.student_code,
            "first_name": s.first_name,
            "last_name": s.last_name,
            "gender": s.gender,
            "status": s.status,
            "class_assignments": class_assignments
        })
    # Build class list for dropdowns
    class_dropdown = [{"code": c.class_code, "class_name": c.class_name} for c in classes]
    return render_template('manage_students.html', students=student_list, classes=class_dropdown)
@app.route('/api/students', methods=['GET'])
@login_required
def get_students():
    students = Student.query.all()
    return jsonify([
        {
            'id': s.id,
            'student_code': s.student_code,
            'first_name': s.first_name,
            'last_name': s.last_name,
            'dob': s.dob.isoformat() if s.dob else None,
            'gender': s.gender,
            'contact_number': s.contact_number,
            'grade_school': s.grade_school,
            'student_email': s.student_email,
            'address': s.address,
            'notes': s.notes,
            'status': s.status
        } for s in students
    ])


@app.route('/api/students/<int:student_id>', methods=['GET'])
@login_required
def get_student(student_id):
    s = Student.query.get_or_404(student_id)
    return jsonify({
        'id': s.id,
        'student_code': s.student_code,
        'first_name': s.first_name,
        'last_name': s.last_name,
        'dob': s.dob.isoformat() if s.dob else None,
        'gender': s.gender,
        'contact_number': s.contact_number,
        'grade_school': s.grade_school,
        'student_email': s.student_email,
        'address': s.address,
        'notes': s.notes,
        'status': s.status
    })


@app.route('/api/students', methods=['POST'])
@login_required
def add_student():
    data = request.json
    # Generate unique student_code in format STU-YYYY-NNNN
    year = datetime.now().year
    prefix = f"STU-{year}-"
    last_student = Student.query.filter(Student.student_code.like(f"{prefix}%")).order_by(Student.student_code.desc()).first()
    if last_student and last_student.student_code:
        try:
            last_num = int(last_student.student_code.split('-')[-1])
        except Exception:
            last_num = 0
    else:
        last_num = 0
    new_num = last_num + 1
    student_code = f"{prefix}{str(new_num).zfill(4)}"
    dob_val = data.get('dob')
    dob_obj = None
    if dob_val:
        try:
            dob_obj = datetime.strptime(dob_val, '%Y-%m-%d').date()
        except Exception:
            dob_obj = None
    s = Student(
        student_code=student_code,
        first_name=data['first_name'],
        last_name=data['last_name'],
        dob=dob_obj,
        gender=data.get('gender'),
        contact_number=data.get('contact_number'),
        grade_school=data.get('grade_school'),
        student_email=data.get('student_email'),
        address=data.get('address'),
        notes=data.get('notes'),
        status=data.get('status', 'active')
    )
    db.session.add(s)
    db.session.commit()
    return jsonify({'id': s.id, 'student_code': s.student_code}), 201


@app.route('/api/students/<int:student_id>', methods=['PUT'])
@login_required
def update_student(student_id):
    s = Student.query.get_or_404(student_id)
    data = request.json
    for field in ['first_name', 'last_name', 'dob', 'gender', 'contact_number', 'grade_school', 'student_email', 'address', 'notes', 'status']:
        if field in data:
            setattr(s, field, data[field])
    db.session.commit()
    return jsonify({'status': 'success'})


@app.route('/api/students/<int:student_id>', methods=['DELETE'])
@login_required
def delete_student(student_id):
    s = Student.query.get_or_404(student_id)
    db.session.delete(s)
    db.session.commit()
    return jsonify({'status': 'deleted'})


# === UPDATED PARENT API ENDPOINTS ===
@app.route('/api/parents', methods=['GET'])
@login_required
def get_parents():
    parents = Parent.query.all()
    return jsonify([
        {
            'id': p.id,
            'student_id': p.student_id,
            'name': p.name,
            'relationship': p.relationship,
            'contact_number': p.contact_number,
            'parent_email': p.parent_email
        } for p in parents
    ])

@app.route('/api/parents/<int:parent_id>', methods=['GET'])
@login_required
def get_parent(parent_id):
    p = Parent.query.get_or_404(parent_id)
    return jsonify({
        'id': p.id,
        'student_id': p.student_id,
        'name': p.name,
        'relationship': p.relationship,
        'contact_number': p.contact_number,
        'parent_email': p.parent_email
    })

@app.route('/api/parents', methods=['POST'])
@login_required
def add_parent():
    data = request.json
    p = Parent(
        student_id=data['student_id'],
        name=data['name'],
        relationship=data.get('relationship'),
        contact_number=data.get('contact_number'),
        parent_email=data.get('parent_email')
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({'id': p.id}), 201

@app.route('/api/parents/<int:parent_id>', methods=['PUT'])
@login_required
def update_parent(parent_id):
    p = Parent.query.get_or_404(parent_id)
    data = request.json
    for field in ['name', 'relationship', 'contact_number', 'parent_email']:
        if field in data:
            setattr(p, field, data[field])
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/api/parents/<int:parent_id>', methods=['DELETE'])
@login_required
def delete_parent(parent_id):
    p = Parent.query.get_or_404(parent_id)
    db.session.delete(p)
    db.session.commit()
    return jsonify({'status': 'deleted'})


# === UPDATED STUDENT CLASS ASSIGNMENT API ENDPOINTS ===
@app.route('/api/assignments', methods=['GET'])
@login_required
def get_assignments():
    assignments = StudentClassAssignment.query.all()
    return jsonify([
        {
            'id': a.id,
            'student_id': a.student_id,
            'class_id': a.class_id,
            'enrolled_from': a.enrolled_from.isoformat() if a.enrolled_from else None,
            'enrolled_to': a.enrolled_to.isoformat() if a.enrolled_to else None,
            'is_primary': a.is_primary
        } for a in assignments
    ])

@app.route('/api/assignments/<int:assignment_id>', methods=['GET'])
@login_required
def get_assignment(assignment_id):
    a = StudentClassAssignment.query.get_or_404(assignment_id)
    return jsonify({
        'id': a.id,
        'student_id': a.student_id,
        'class_id': a.class_id,
        'enrolled_from': a.enrolled_from.isoformat() if a.enrolled_from else None,
        'enrolled_to': a.enrolled_to.isoformat() if a.enrolled_to else None,
        'is_primary': a.is_primary
    })

@app.route('/api/assignments', methods=['POST'])
@login_required
def add_assignment():
    data = request.json
    enrolled_from = None
    enrolled_to = None
    if data.get('enrolled_from'):
        try:
            enrolled_from = datetime.strptime(data['enrolled_from'], '%Y-%m-%d').date()
        except Exception:
            enrolled_from = None
    if data.get('enrolled_to'):
        try:
            enrolled_to = datetime.strptime(data['enrolled_to'], '%Y-%m-%d').date()
        except Exception:
            enrolled_to = None
    a = StudentClassAssignment(
        student_id=data['student_id'],
        class_id=data['class_id'],
        enrolled_from=enrolled_from,
        enrolled_to=enrolled_to,
        is_primary=data.get('is_primary', False)
    )
    db.session.add(a)
    db.session.commit()
    return jsonify({'id': a.id}), 201

@app.route('/api/assignments/<int:assignment_id>', methods=['PUT'])
@login_required
def update_assignment(assignment_id):
    a = StudentClassAssignment.query.get_or_404(assignment_id)
    data = request.json
    for field in ['student_id', 'class_id', 'is_primary']:
        if field in data:
            setattr(a, field, data[field])
    # Handle date fields
    if 'enrolled_from' in data:
        try:
            a.enrolled_from = datetime.strptime(data['enrolled_from'], '%Y-%m-%d').date() if data['enrolled_from'] else None
        except Exception:
            a.enrolled_from = None
    if 'enrolled_to' in data:
        try:
            a.enrolled_to = datetime.strptime(data['enrolled_to'], '%Y-%m-%d').date() if data['enrolled_to'] else None
        except Exception:
            a.enrolled_to = None
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/api/assignments/<int:assignment_id>', methods=['DELETE'])
@login_required
def delete_assignment(assignment_id):
    a = StudentClassAssignment.query.get_or_404(assignment_id)
    db.session.delete(a)
    db.session.commit()
    return jsonify({'status': 'deleted'})


# === UPDATED STUDENT FEE API ENDPOINTS ===
@app.route('/api/fees', methods=['GET'])
@login_required
def get_fees():
    fees = StudentFee.query.all()
    return jsonify([
        {
            'id': f.id,
            'student_id': f.student_id,
            'class_id': f.class_id,
            'fee_type': f.fee_type,
            'amount_due': f.amount_due,
            'amount_paid': f.amount_paid,
            'discount': f.discount,
            'due_date': f.due_date.isoformat() if f.due_date else None,
            'payment_status': f.payment_status,
            'notes': f.notes
        } for f in fees
    ])

@app.route('/api/fees/<int:fee_id>', methods=['GET'])
@login_required
def get_fee(fee_id):
    f = StudentFee.query.get_or_404(fee_id)
    return jsonify({
        'id': f.id,
        'student_id': f.student_id,
        'class_id': f.class_id,
        'fee_type': f.fee_type,
        'amount_due': f.amount_due,
        'amount_paid': f.amount_paid,
        'discount': f.discount,
        'due_date': f.due_date.isoformat() if f.due_date else None,
        'payment_status': f.payment_status,
        'notes': f.notes
    })

@app.route('/api/fees', methods=['POST'])
@login_required
def add_fee():
    data = request.json
    due_date = None
    if data.get('due_date'):
        try:
            due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
        except Exception:
            due_date = None
    f = StudentFee(
        student_id=data['student_id'],
        class_id=data.get('class_id'),
        fee_type=data.get('fee_type'),
        amount_due=data.get('amount_due', 0.0),
        amount_paid=data.get('amount_paid', 0.0),
        discount=data.get('discount', 0.0),
        due_date=due_date,
        payment_status=data.get('payment_status', 'unpaid'),
        notes=data.get('notes')
    )
    db.session.add(f)
    db.session.commit()
    return jsonify({'id': f.id}), 201

@app.route('/api/fees/<int:fee_id>', methods=['PUT'])
@login_required
def update_fee(fee_id):
    f = StudentFee.query.get_or_404(fee_id)
    data = request.json
    for field in ['student_id', 'class_id', 'fee_type', 'amount_due', 'amount_paid', 'discount', 'payment_status', 'notes']:
        if field in data:
            setattr(f, field, data[field])
    # Handle due_date
    if 'due_date' in data:
        try:
            f.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date() if data['due_date'] else None
        except Exception:
            f.due_date = None
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/api/fees/<int:fee_id>', methods=['DELETE'])
@login_required
def delete_fee(fee_id):
    f = StudentFee.query.get_or_404(fee_id)
    db.session.delete(f)
    db.session.commit()
    return jsonify({'status': 'deleted'})

# === ATTENDANCE API ENDPOINTS ===
@app.route('/api/attendance', methods=['GET'])
@login_required
def get_attendance():
    records = Attendance.query.all()
    return jsonify([
        {
            'id': a.id,
            'student_id': a.student_id,
            'class_code': a.class_code,
            'date': a.date.isoformat() if a.date else None,
            'status': a.status,
            'notes': a.notes
        } for a in records
    ])

@app.route('/api/attendance/<int:attendance_id>', methods=['GET'])
@login_required
def get_attendance_record(attendance_id):
    a = Attendance.query.get_or_404(attendance_id)
    return jsonify({
        'id': a.id,
        'student_id': a.student_id,
        'class_code': a.class_code,
        'date': a.date.isoformat() if a.date else None,
        'status': a.status,
        'notes': a.notes
    })

@app.route('/api/attendance', methods=['POST'])
@login_required
def add_attendance():
    data = request.json
    a = Attendance(
        student_id=data['student_id'],
        class_code=data['class_code'],
        date=data.get('date'),
        status=data.get('status'),
        notes=data.get('notes')
    )
    db.session.add(a)
    db.session.commit()
    return jsonify({'id': a.id}), 201

@app.route('/api/attendance/<int:attendance_id>', methods=['PUT'])
@login_required
def update_attendance(attendance_id):
    a = Attendance.query.get_or_404(attendance_id)
    data = request.json
    for field in ['student_id', 'class_code', 'date', 'status', 'notes']:
        if field in data:
            setattr(a, field, data[field])
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/api/attendance/<int:attendance_id>', methods=['DELETE'])
@login_required
def delete_attendance(attendance_id):
    a = Attendance.query.get_or_404(attendance_id)
    db.session.delete(a)
    db.session.commit()
    return jsonify({'status': 'deleted'})

# === PAYMENT API ENDPOINTS ===
@app.route('/api/payments', methods=['GET'])
@login_required
def get_payments():
    payments = Payment.query.all()
    return jsonify([
        {
            'id': p.id,
            'student_id': p.student_id,
            'fee_id': p.fee_id,
            'amount': p.amount,
            'date': p.date.isoformat() if p.date else None,
            'method': p.method,
            'reference': p.reference,
            'notes': p.notes
        } for p in payments
    ])

@app.route('/api/payments/<int:payment_id>', methods=['GET'])
@login_required
def get_payment(payment_id):
    p = Payment.query.get_or_404(payment_id)
    return jsonify({
        'id': p.id,
        'student_id': p.student_id,
        'fee_id': p.fee_id,
        'amount': p.amount,
        'date': p.date.isoformat() if p.date else None,
        'method': p.method,
        'reference': p.reference,
        'notes': p.notes
    })

@app.route('/api/payments', methods=['POST'])
@login_required
def add_payment():
    data = request.json
    p = Payment(
        student_id=data['student_id'],
        fee_id=data.get('fee_id'),
        amount=data.get('amount', 0.0),
        date=data.get('date'),
        method=data.get('method'),
        reference=data.get('reference'),
        notes=data.get('notes')
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({'id': p.id}), 201

@app.route('/api/payments/<int:payment_id>', methods=['PUT'])
@login_required
def update_payment(payment_id):
    p = Payment.query.get_or_404(payment_id)
    data = request.json
    for field in ['student_id', 'fee_id', 'amount', 'date', 'method', 'reference', 'notes']:
        if field in data:
            setattr(p, field, data[field])
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/api/payments/<int:payment_id>', methods=['DELETE'])
@login_required
def delete_payment(payment_id):
    p = Payment.query.get_or_404(payment_id)
    db.session.delete(p)
    db.session.commit()
    return jsonify({'status': 'deleted'})

@app.route("/ping", methods=["GET"])
def ping():
    print("✅ Ping received")
    return "pong"

@app.route("/manage_classes")
@login_required
def manage_classes():
    # Fetch all classes from the database
    class_objs = Class.query.all()
    # For each class, fetch the latest GoogleClassroomCourse (if any)
    classes = {}
    for c in class_objs:
        gclass = GoogleClassroomCourse.query.filter_by(class_id=c.id).order_by(GoogleClassroomCourse.created_at.desc()).first()
        classes[c.class_code] = {
            "class_name": c.class_name,
            "subject": c.subject,
            "year_level": c.year_level,
            "batch": c.batch,
            "sub_batch": c.sub_batch,
            "class_type": c.class_type,
            "description": c.description,
            "playlist_id": c.playlist_id,
            "gclass_linked": bool(gclass),
            "courseId": gclass.course_id if gclass else None,
            "joinCode": gclass.join_code if gclass else None,
            "classroom_name": gclass.name if gclass else None,
            "classroom_section": gclass.section if gclass else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            "class_created": c.class_created.isoformat() if c.class_created else None,
            "class_teacher": c.class_teacher,
            "class_day": c.class_day,
            "class_time": c.class_time,
            "class_location": c.class_location,
            "class_status": c.class_status
        }
    return render_template("manage_classes.html", classes=classes)
    return render_template('manage_students.html', students=student_list, classes=classes)

# --- Admin Mapping and Sync Routes ---

@app.route('/admin/mapping')
@login_required
@admin_required
def admin_mapping():
    # Fetch all classes
    classes = Class.query.all()
    # Fetch all Google Classroom courses
    gclass_courses = GoogleClassroomCourse.query.all()
    # Fetch all YouTube playlists (from Video table, grouped by playlist_id)
    from sqlalchemy import func
    playlists = db.session.query(
        Video.youtube_playlist_id, func.max(Video.title)
    ).group_by(Video.youtube_playlist_id).all()
    return render_template(
        'admin_mapping.html',
        classes=classes,
        gclass_courses=gclass_courses,
        playlists=playlists
    )

@app.route('/api/google_classroom_courses', methods=['GET'])
@login_required
@admin_required
def api_google_classroom_courses():
    courses = GoogleClassroomCourse.query.all()
    return jsonify([
        {
            'id': c.id,
            'course_id': c.course_id,
            'name': c.name,
            'section': c.section,
            'join_code': c.join_code,
            'class_id': c.class_id
        } for c in courses
    ])

@app.route('/api/youtube_playlists', methods=['GET'])
@login_required
@admin_required
def api_youtube_playlists():
    # Get unique playlist IDs from Video table
    from sqlalchemy import func
    playlists = db.session.query(
        Video.youtube_playlist_id, func.max(Video.title)
    ).group_by(Video.youtube_playlist_id).all()
    return jsonify([
        {
            'playlist_id': pid,
            'title': title
        } for pid, title in playlists if pid
    ])

@app.route('/api/map_class_resources/<class_code>', methods=['POST'])
@login_required
@admin_required
def api_map_class_resources(class_code):
    data = request.json
    cls = Class.query.filter_by(class_code=class_code).first()
    if not cls:
        return jsonify({'status': 'error', 'message': 'Class not found'}), 404

    # Map Google Classroom course
    gclass_id = data.get('google_classroom_course_id')
    if gclass_id:
        gclass = GoogleClassroomCourse.query.get(gclass_id)
        if gclass:
            gclass.class_id = cls.id
            db.session.commit()

    # Map YouTube playlist
    playlist_id = data.get('youtube_playlist_id')
    if playlist_id:
        # Update all videos with this playlist to point to this class
        Video.query.filter_by(youtube_playlist_id=playlist_id).update({'class_id': cls.id})
        db.session.commit()

    return jsonify({'status': 'success', 'message': 'Resources mapped successfully.'})

# --- SYNC ROUTES FOR ADMIN MAPPING TOOL ---

@app.route('/api/sync_google_classrooms', methods=['POST'])
@login_required
@admin_required
def sync_google_classrooms():
    data = request.json or {}
    teacher_email = data.get('teacher_email')
    if not teacher_email:
        return jsonify({'status': 'error', 'message': 'Teacher email required'}), 400

    try:
        # Get integration account for this teacher
        integration_account = GoogleIntegrationAccount.query.filter_by(google_email=teacher_email).first()
        if not integration_account:
            return jsonify({'status': 'error', 'message': 'No integration account found for this email'}), 404

        service = get_classroom_service()  # You may need to pass credentials for the teacher
        courses = service.courses().list(teacherId=teacher_email, courseStates=['ACTIVE']).execute().get('courses', [])
        added, updated = 0, 0
        for course in courses:
            existing = GoogleClassroomCourse.query.filter_by(course_id=course['id']).first()
            if existing:
                # Optionally update fields
                existing.name = course.get('name')
                existing.section = course.get('section')
                existing.join_code = course.get('enrollmentCode')
                existing.integration_account_id = integration_account.id
                updated += 1
            else:
                new_course = GoogleClassroomCourse(
                    course_id=course['id'],
                    name=course.get('name'),
                    section=course.get('section'),
                    join_code=course.get('enrollmentCode'),
                    integration_account_id=integration_account.id,
                    created_by=current_user.id,
                    created_at=datetime.utcnow()
                )
                db.session.add(new_course)
                added += 1
        db.session.commit()
        return jsonify({'status': 'success', 'added': added, 'updated': updated})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/sync_youtube_playlists', methods=['POST'])
@login_required
@admin_required
def sync_youtube_playlists():
    data = request.json or {}
    teacher_email = data.get('teacher_email')
    if not teacher_email:
        return jsonify({'status': 'error', 'message': 'Teacher email required'}), 400

    try:
        # Get integration account for this teacher
        integration_account = GoogleIntegrationAccount.query.filter_by(google_email=teacher_email).first()
        if not integration_account:
            return jsonify({'status': 'error', 'message': 'No integration account found for this email'}), 404

        youtube = get_authenticated_service()  # You may need to pass credentials for the teacher
        playlists = []
        nextPageToken = None
        while True:
            pl_request = youtube.playlists().list(
                part="id,snippet",
                mine=True,
                maxResults=50,
                pageToken=nextPageToken
            )
            pl_response = pl_request.execute()
            playlists.extend(pl_response.get('items', []))
            nextPageToken = pl_response.get('nextPageToken')
            if not nextPageToken:
                break

        added, updated = 0, 0
        for pl in playlists:
            pl_id = pl['id']
            title = pl['snippet']['title']
            # Store as a Video row with only playlist_id and title, or create a Playlist model if you have one
            existing = Video.query.filter_by(youtube_playlist_id=pl_id).first()
            if not existing:
                new_video = Video(
                    video_id=str(uuid.uuid4()),
                    title=title,
                    youtube_playlist_id=pl_id,
                    integration_account_id=integration_account.id,
                    uploaded_by=current_user.id,
                    published_at=datetime.utcnow()
                )
                db.session.add(new_video)
                added += 1
            else:
                existing.title = title
                updated += 1
        db.session.commit()
        return jsonify({'status': 'success', 'added': added, 'updated': updated})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
    
# === Run App ===
if __name__ == "__main__":
    app.run(debug=False)
