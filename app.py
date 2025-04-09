import os
from pydoc import text
from flask import Flask, flash, render_template, request, redirect, url_for  
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.exc import IntegrityError





app = Flask(__name__)
app.secret_key = 'zayd_secret_key_123'

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///employees.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
UPLOAD_FOLDER = 'static/images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)


# Employee Table
class Employee(db.Model):  
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    job_role_id = db.Column(db.Integer, db.ForeignKey('job_role.id'), nullable=False)
    salary = db.Column(db.Float, nullable=False)
    date_joined = db.Column(db.Date, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    photo = db.Column(db.String(255), nullable=True) 

# Department Table
class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    employees = db.relationship('Employee', backref='department', lazy=True)

# Job Role Table
class JobRole(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    employees = db.relationship('Employee', backref='job_role', lazy=True)

#attendance table
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    status = db.Column(db.String(10), nullable=False)   
    employee = db.relationship('Employee', backref='attendance_records')



# Create Tables

with app.app_context():
    db.create_all


@app.route("/")
def home():
    employees = Employee.query.all()  
    departments=Department.query.all()
    return render_template("index.html", employees=employees ,departments=departments)

 
 


#add employee route
@app.route("/add_employee", methods=["GET", "POST"])
def add_employee():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        
        # Validate Department ID
        department_id = request.form.get("Department")
        if not department_id or not department_id.isdigit():
            return "Error: Invalid Department ID", 400
        department_id = int(department_id)

        # Validate Job Role ID
        job_role_id = request.form.get("JobRole")
        if not job_role_id or not job_role_id.isdigit():
            return "Error: Invalid Job Role ID", 400
        job_role_id = int(job_role_id)

        # Validate Salary
        try:
            salary = float(request.form.get("Salary"))
        except ValueError:
            return "Error: Salary must be a valid number", 400

        # Validate Status
        is_active = request.form.get("is_active") == "1"

        # Validate Joining Date
        joining_date_str = request.form.get("Joiningdate")
        try:
            joining_date = datetime.strptime(joining_date_str, "%Y-%m-%d")
        except ValueError:
            return "Error: Invalid Joining Date Format", 400

        # Handle Profile Picture Upload
        profile_picture = request.files.get("photo")
        if profile_picture and profile_picture.filename:
            photo_path = os.path.join(app.config["UPLOAD_FOLDER"], profile_picture.filename)
            profile_picture.save(photo_path)
        else:
            photo_path = "default-avatar.png"


        # Save Employee
        employee = Employee(
            name=name,
            email=email,
            phone=phone,
            department_id=department_id,
            job_role_id=job_role_id,
            salary=salary,
            date_joined=joining_date,
            is_active=is_active,
            photo=photo_path
        )

        db.session.add(employee)
        db.session.commit()
        flash(f"{employee.name} has been added successfully.", "success")

        return redirect(url_for("home"))

    departments = Department.query.all()
    job_roles = JobRole.query.all()
    return render_template("add_employee.html", departments=departments, job_roles=job_roles)

#show employee detail 
@app.route('/employee_details/<int:employee_id>', methods=["GET"])
def employee_details(employee_id):
        employee = Employee.query.get(employee_id)
        return render_template('employee_details.html', employee=employee)
    
#update employee detail 
@app.route('/update_employee_details/<int:employee_id>', methods=["GET"])
def update_employee_details(employee_id):
        employee = Employee.query.get(employee_id)
        return render_template('update_employee_details.html', employee=employee)


@app.route('/update_employee_details/<int:employee_id>', methods=["POST"])
def update_employee_post(employee_id):
    employee = Employee.query.get_or_404(employee_id)

    phone = request.form['phone']
    existing = Employee.query.filter_by(phone=phone).first()
    if existing and existing.id != employee.id:
        flash("Phone number already exists for another employee.", "danger")
        return redirect(url_for('update_employee_details', employee_id=employee.id))

    # Update values
    employee.name = request.form['name']
    employee.email = request.form['email']
    employee.phone = phone
    employee.department_id = request.form['department_id']
    employee.job_role_id = request.form['job_role_id']
    employee.salary = request.form['salary']
    employee.is_active = bool(int(request.form['is_active']))

    upload_folder = 'static/images'
    os.makedirs(upload_folder, exist_ok=True)

    photo_file = request.files.get('photo')
    if photo_file and photo_file.filename:
        filename = photo_file.filename
        file_path = os.path.join(upload_folder, filename)
        photo_file.save(file_path)
        employee.photo = filename

    try:
        db.session.commit()
        flash("Employee updated successfully!", "success")
    except IntegrityError:
        db.session.rollback()
        flash("Something went wrong. Try again!", "danger")

    return redirect(url_for('home'))

#manage employee route
@app.route("/manage_employees")
def manage_employees():
    selected_department = request.args.get("department", type=int)
    selected_job_role = request.args.get("job_role", type=int)

    departments = Department.query.all()
    job_roles = JobRole.query.all()

    query = Employee.query

    if selected_department:
        query = query.filter_by(department_id=selected_department)

    if selected_job_role:
        query = query.filter_by(job_role_id=selected_job_role)

    employees = query.all()

    return render_template("manage_employees.html",
                           employees=employees,
                           departments=departments,
                           job_roles=job_roles,
                           selected_department=selected_department,
                           selected_job_role=selected_job_role)


#attendance route
@app.route("/mark_attendance", methods=["GET", "POST"])
def mark_attendance():
    employees = Employee.query.all()

    if request.method == "POST":
        date_str = request.form.get("date")
        date = datetime.strptime(date_str, "%Y-%m-%d").date()

        # Check if attendance already marked
        existing = Attendance.query.filter_by(date=date).first()
        if existing:
            flash("Attendance already marked for this date.", "warning")
            return redirect(url_for("mark_attendance"))

        for emp in employees:
            status = request.form.get(f"status_{emp.id}")
            attendance = Attendance(employee_id=emp.id, date=date, status=status)
            db.session.add(attendance)

        db.session.commit()
        flash("Attendance marked successfully!", "success")
        return redirect(url_for('attendance_history'))

    return render_template("mark_attendance.html", employees=employees)

#attendance histroy
@app.route("/attendance_history")
def attendance_history():
    attendance_records = Attendance.query.order_by(Attendance.date.desc()).all()
    employees = {emp.id: emp.name for emp in Employee.query.all()}
    return render_template("attendance_history.html", attendance_records=attendance_records, employees=employees)



#delete employee 
@app.route("/delete_employee/<int:employee_id>", methods=["GET", "POST"])
def delete_employee(employee_id):
    employee = Employee.query.get(employee_id)
    if employee:
        db.session.delete(employee)
        db.session.commit()
        flash(f"{employee.name} has been deleted successfully.", "success")
    else:
        flash("Employee not found.", "danger")

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
