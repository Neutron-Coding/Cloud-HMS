from flask import render_template, redirect, url_for, request, flash, abort
from flask_login import login_user, logout_user, login_required, current_user
from flask import current_app as app
from application.models import db, User, Admin, Doctor, Patient, Department, Appointment, Treatment
from datetime import datetime, timedelta
from sqlalchemy import or_


def _get_doctor_by_identifier_or_404(identifier: int) -> Doctor:
    """Return doctor by primary key or linked user id; abort if missing."""
    doctor = Doctor.query.filter_by(doctor_id=identifier).first()
    if not doctor:
        doctor = Doctor.query.get(identifier)
    if not doctor:
        abort(404)
    return doctor


def _get_patient_by_identifier_or_404(identifier: int) -> Patient:
    patient = Patient.query.filter_by(patient_id=identifier).first()
    if not patient:
        patient = Patient.query.get(identifier)
    if not patient:
        abort(404)
    return patient

# ==================== HOME & INDEX ROUTES ====================

@app.route('/')
@app.route('/index')
def index():
    departments = Department.query.all()
    return render_template('index.html', departments=departments)

@app.route('/home')
def home():
    departments = Department.query.all()
    return render_template('home.html', departments=departments)

# ==================== ADMIN ROUTES ====================

# ADMIN LOGIN
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username') or request.form.get('u_name')
        password = request.form.get('password') or request.form.get('pwd')
        
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and admin.password == password: 
            user = User.query.get(admin.admin_id)
            if user:
                login_user(user)
                return redirect(url_for('admin_dashboard'))
        
        return render_template('admin_login.html', error="Invalid credentials")
    
    return render_template('admin_login.html')

# ADMIN DASHBOARD
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.user_role != 1:
        return redirect(url_for('home'))
    
    admin = Admin.query.filter_by(admin_id=current_user.id).first()
    
    total_departments = Department.query.count()
    total_doctors = Doctor.query.count()
    total_patients = Patient.query.count()
    total_appointments = Appointment.query.filter(Appointment.patient_id != 999).count()
    booked_appointments = Appointment.query.filter_by(status='Booked').filter(Appointment.patient_id != 999).count()
    completed_appointments = Appointment.query.filter_by(status='Completed').count()
    
    recent_appointments = Appointment.query.filter(
        Appointment.patient_id != 999
    ).order_by(
        Appointment.appointment_date.desc()
    ).limit(5).all()
    
    return render_template('admin_dashboard.html',
                        admin=admin,
                        total_departments=total_departments,
                        total_doctors=total_doctors,
                        total_patients=total_patients,
                        total_appointments=total_appointments,
                        booked_appointments=booked_appointments,
                        completed_appointments=completed_appointments,
                        recent_appointments=recent_appointments)

# ADMIN LOGOUT
@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('home'))

# ==================== ADMIN - DOCTOR MANAGEMENT ====================

# VIEW ALL DOCTORS
@app.route('/admin/doctors')
@login_required
def admin_manage_doctors():
    if current_user.user_role != 1:
        return redirect(url_for('home'))
    
    admin = Admin.query.filter_by(admin_id=current_user.id).first()
    doctors = Doctor.query.all()
    departments = Department.query.all()
    
    return render_template('admin_manage_doctors.html', 
                        admin=admin, 
                        doctors=doctors,
                        departments=departments)

# ADD DOCTOR
@app.route('/admin/doctor/add', methods=['POST'])
@login_required
def admin_add_doctor():
    if current_user.user_role != 1:
        return redirect(url_for('home'))
    
    username = request.form.get('username')
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    password = request.form.get('password')
    phone = request.form.get('phone')
    specialization = request.form.get('specialization')
    qualification = request.form.get('qualification')
    experience = request.form.get('experience')
    department_id = request.form.get('department_id')
    
    if not all([username, full_name, email, password, specialization, department_id]):
        flash("All required fields must be filled", "error")
        return redirect(url_for('admin_manage_doctors'))
    
    if User.query.filter_by(username=username).first():
        flash("Username already exists. Please choose another.", "error")
        return redirect(url_for('admin_manage_doctors'))
    
    if User.query.filter_by(email=email).first():
        flash("Email already registered", "error")
        return redirect(url_for('admin_manage_doctors'))
    
    user = User(
        username=username,
        email=email,
        password=password,
        user_role=2
    )
    db.session.add(user)
    db.session.flush()
    
    doctor = Doctor(
        doctor_id=user.id,
        username=username,
        full_name=full_name,
        email=email,
        password=user.password,
        phone=phone,
        specialization=specialization,
        qualification=qualification,
        experience=int(experience) if (experience and experience.isdigit()) else None,
        department_id=department_id
    )
    db.session.add(doctor)
    db.session.commit()
    
    flash("Doctor added successfully", "success")
    return redirect(url_for('admin_manage_doctors'))

# VIEW SINGLE DOCTOR
@app.route('/admin/doctor/<int:doctor_id>')
@login_required
def admin_view_doctor(doctor_id):
    if current_user.user_role != 1:
        return redirect(url_for('home'))
    
    admin = Admin.query.filter_by(admin_id=current_user.id).first()
    doctor = _get_doctor_by_identifier_or_404(doctor_id)
    
    # Get doctor's appointments
    appointments = Appointment.query.filter(
        or_(
            Appointment.doctor_id == doctor.id,
            Appointment.doctor_id == doctor.doctor_id
        )
    ).order_by(Appointment.appointment_date.desc()).all()
    
    return render_template('admin_view_doctor.html', 
                        admin=admin, 
                        doctor=doctor, 
                        appointments=appointments)

# UPDATE DOCTOR
@app.route('/admin/doctor/<int:doctor_id>/update', methods=['GET', 'POST'])
@login_required
def admin_update_doctor(doctor_id):
    if current_user.user_role != 1:
        return redirect(url_for('home'))
    
    admin = Admin.query.filter_by(admin_id=current_user.id).first()
    doctor = _get_doctor_by_identifier_or_404(doctor_id)
    departments = Department.query.all()
    
    if request.method == 'POST':
        new_username = request.form.get('username')
        doctor.full_name = request.form.get('full_name')
        doctor.email = request.form.get('email')
        doctor.phone = request.form.get('phone')
        doctor.specialization = request.form.get('specialization')
        doctor.qualification = request.form.get('qualification')
        experience_val = request.form.get('experience')
        if experience_val is not None and experience_val != "":
            try:
                doctor.experience = int(experience_val)
            except ValueError:
                flash("Experience must be a valid number", "error")
                return redirect(url_for('admin_update_doctor', doctor_id=doctor_id))
        doctor.department_id = request.form.get('department_id')
        
        
        user = User.query.get(doctor.doctor_id)
        if user:
            
            if new_username and new_username != user.username:
                existing_user = User.query.filter_by(username=new_username).first()
                if existing_user:
                    flash("Username already exists. Please choose another.", "error")
                    return redirect(url_for('admin_update_doctor', doctor_id=doctor_id))
                user.username = new_username
                doctor.username = new_username
            user.email = doctor.email
        
        db.session.commit()
        flash("Doctor updated successfully", "success")
        return redirect(url_for('admin_manage_doctors'))
    
    return render_template('admin_update_doctor.html', 
                        admin=admin, 
                        doctor=doctor, 
                        departments=departments)

# DELETE DOCTOR
@app.route('/admin/doctor/<int:doctor_id>/delete', methods=['POST'])
@login_required
def admin_delete_doctor(doctor_id):
    if current_user.user_role != 1:
        return redirect(url_for('home'))
    
    doctor = _get_doctor_by_identifier_or_404(doctor_id)
    user = User.query.get(doctor.doctor_id)
    
    
    doctor_appt_filter = or_(
        Appointment.doctor_id == doctor.id,
        Appointment.doctor_id == doctor.doctor_id
    )
    appointments = Appointment.query.filter(doctor_appt_filter).all()
    for apt in appointments:
        Treatment.query.filter_by(appointment_id=apt.id).delete()
    Appointment.query.filter(doctor_appt_filter).delete(synchronize_session=False)
    
    db.session.delete(doctor)
    if user:
        db.session.delete(user)
    db.session.commit()
    
    flash("Doctor deleted successfully", "success")
    return redirect(url_for('admin_manage_doctors'))

# ADMIN BLACKLIST/UNBLACKLIST DOCTOR
@app.route('/admin/doctor/<int:doctor_id>/toggle-blacklist', methods=['POST'])
@login_required
def admin_toggle_doctor_blacklist(doctor_id):
    if current_user.user_role != 1:
        return redirect(url_for('home'))
    
    doctor = _get_doctor_by_identifier_or_404(doctor_id)
    
    
    doctor.flagged = not doctor.flagged
    db.session.commit()
    
    status = "blacklisted" if doctor.flagged else "unblacklisted"
    flash(f"Doctor {doctor.full_name} has been {status}", "success")
    return redirect(url_for('admin_manage_doctors'))

# ==================== ADMIN - PATIENT MANAGEMENT ====================

# VIEW ALL PATIENTS
@app.route('/admin/patients')
@login_required
def admin_manage_patients():
    if current_user.user_role != 1:
        return redirect(url_for('home'))
    
    admin = Admin.query.filter_by(admin_id=current_user.id).first()
    patients = Patient.query.all()
    
    return render_template('admin_manage_patients.html', 
                        admin=admin, 
                        patients=patients)

# ADD PATIENT 
@app.route('/admin/patient/add', methods=['POST'])
@login_required
def admin_add_patient():
    if current_user.user_role != 1:
        return redirect(url_for('home'))
    
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    password = request.form.get('password')
    phone = request.form.get('phone')
    date_of_birth = request.form.get('date_of_birth')
    gender = request.form.get('gender')
    blood_group = request.form.get('blood_group')
    address = request.form.get('address')
    
    if not all([full_name, email, password]):
        flash("Name, email and password are required", "error")
        return redirect(url_for('admin_manage_patients'))
    
    if User.query.filter_by(email=email).first():
        flash("Email already registered", "error")
        return redirect(url_for('admin_manage_patients'))
    
    username = email.split('@')[0]
    if User.query.filter_by(username=username).first():
        username = email
    
    # Create User account
    user = User(
        username=username,  
        email=email,
        password=password,
        user_role=3
    )
    db.session.add(user)
    db.session.flush()
    
    # Convert date_of_birth
    dob = None
    if date_of_birth:
        try:
            dob = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
        except:
            pass
    
    # Create Patient profile
    patient = Patient(
        patient_id=user.id,
        full_name=full_name,
        username=user.username,
        email=email,
        password=user.password,
        phone=phone,
        date_of_birth=dob,
        gender=gender,
        blood_group=blood_group,
        address=address
    )
    db.session.add(patient)
    db.session.commit()
    
    flash("Patient added successfully", "success")
    return redirect(url_for('admin_manage_patients'))

# VIEW SINGLE PATIENT
@app.route('/admin/patient/<int:patient_id>')
@login_required
def admin_view_patient(patient_id):
    if current_user.user_role != 1:
        return redirect(url_for('home'))
    
    admin = Admin.query.filter_by(admin_id=current_user.id).first()
    patient = _get_patient_by_identifier_or_404(patient_id)
    
    appointments = Appointment.query.filter_by(patient_id=patient.id).order_by(
        Appointment.appointment_date.desc()
    ).all()
    
    return render_template('admin_view_patient.html', 
                        admin=admin, 
                        patient=patient, 
                        appointments=appointments)

# UPDATE PATIENT
@app.route('/admin/patient/<int:patient_id>/update', methods=['GET', 'POST'])
@login_required
def admin_update_patient(patient_id):
    if current_user.user_role != 1:
        return redirect(url_for('home'))
    
    admin = Admin.query.filter_by(admin_id=current_user.id).first()
    patient = _get_patient_by_identifier_or_404(patient_id)
    
    if request.method == 'POST':
        new_username = request.form.get('username')
        patient.full_name = request.form.get('full_name')
        patient.email = request.form.get('email')
        patient.phone = request.form.get('phone')
        patient.gender = request.form.get('gender')
        patient.blood_group = request.form.get('blood_group')
        patient.address = request.form.get('address')
        
        date_of_birth = request.form.get('date_of_birth')
        if date_of_birth:
            try:
                patient.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
            except:
                pass
        
        user = User.query.get(patient.patient_id)
        if user:
            if new_username and new_username != user.username:
                existing_user = User.query.filter_by(username=new_username).first()
                if existing_user:
                    flash("Username already exists. Please choose another.", "error")
                    return redirect(url_for('admin_update_patient', patient_id=patient_id))
                user.username = new_username
                patient.username = new_username
            user.email = patient.email
        
        db.session.commit()
        flash("Patient updated successfully", "success")
        return redirect(url_for('admin_manage_patients'))
    
    return render_template('admin_update_patient.html', 
                        admin=admin, 
                        patient=patient)

# DELETE PATIENT
@app.route('/admin/patient/<int:patient_id>/delete', methods=['POST'])
@login_required
def admin_delete_patient(patient_id):
    if current_user.user_role != 1:
        return redirect(url_for('home'))
    
    patient = _get_patient_by_identifier_or_404(patient_id)
    user = User.query.get(patient.patient_id)
    
    patient_appt_filter = or_(
        Appointment.patient_id == patient.id,
        Appointment.patient_id == patient.patient_id
    )
    appointments = Appointment.query.filter(patient_appt_filter).all()
    for apt in appointments:
        Treatment.query.filter_by(appointment_id=apt.id).delete()
    Appointment.query.filter(patient_appt_filter).delete(synchronize_session=False)
    
    db.session.delete(patient)
    if user:
        db.session.delete(user)
    db.session.commit()
    
    flash("Patient deleted successfully", "success")
    return redirect(url_for('admin_manage_patients'))

# ADMIN BLACKLIST/UNBLACKLIST PATIENT
@app.route('/admin/patient/<int:patient_id>/toggle-blacklist', methods=['POST'])
@login_required
def admin_toggle_patient_blacklist(patient_id):
    if current_user.user_role != 1:
        return redirect(url_for('home'))
    
    patient = _get_patient_by_identifier_or_404(patient_id)
    
    patient.flagged = not patient.flagged
    db.session.commit()
    
    status = "blacklisted" if patient.flagged else "unblacklisted"
    flash(f"Patient {patient.full_name} has been {status}", "success")
    return redirect(url_for('admin_manage_patients'))

# ==================== ADMIN - APPOINTMENT MANAGEMENT ====================

# VIEW ALL APPOINTMENTS
@app.route('/admin/appointments', methods=['GET', 'POST'])
@login_required
def admin_manage_appointments():
    if current_user.user_role != 1:
        return redirect(url_for('home'))
    
    admin = Admin.query.filter_by(admin_id=current_user.id).first()
    
    if request.method == 'POST':
        patient_id = request.form.get('patient_id')
        doctor_id = request.form.get('doctor_id')
        appointment_date = request.form.get('appointment_date')
        appointment_time = request.form.get('appointment_time')
        reason = request.form.get('reason')
        status = request.form.get('status', 'Booked')
        
        if not all([patient_id, doctor_id, appointment_date, appointment_time]):
            flash("All fields are required", "error")
            return redirect(url_for('admin_manage_appointments'))
        
        patient_check = Patient.query.filter_by(id=patient_id).first()
        doctor_check = Doctor.query.filter_by(id=doctor_id).first()
        
        if patient_check and patient_check.flagged:
            flash("Cannot book appointment. Patient is blacklisted.", "error")
            return redirect(url_for('admin_manage_appointments'))
        
        if doctor_check and doctor_check.flagged:
            flash("Cannot book appointment. Doctor is blacklisted.", "error")
            return redirect(url_for('admin_manage_appointments'))
        
        try:
            appointment_date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
        except:
            flash("Invalid date format", "error")
            return redirect(url_for('admin_manage_appointments'))
        
        allowed_times = ['10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00']
        if appointment_time not in allowed_times:
            flash("Invalid time slot. Appointments are only available between 10 AM and 6 PM.", "error")
            return redirect(url_for('admin_manage_appointments'))
        
        #PREVENT MULTIPLE APPOINTMENTS
        existing = Appointment.query.filter_by(
            doctor_id=doctor_id,
            appointment_date=appointment_date_obj,
            appointment_time=appointment_time
        ).filter(Appointment.status != 'Cancelled').first()
        
        if existing:
            flash("This time slot is already booked for the doctor. Please choose another time.", "error")
            return redirect(url_for('admin_manage_appointments'))
        
        appointment = Appointment(
            patient_id=patient_id,
            doctor_id=doctor_id,
            appointment_date=appointment_date_obj,
            appointment_time=appointment_time,
            reason=reason,
            status=status
        )
        db.session.add(appointment)
        db.session.commit()
        
        flash("Appointment added successfully", "success")
        return redirect(url_for('admin_manage_appointments'))
    
    filter_type = request.args.get('filter', 'all')
    today = datetime.now().date()
    
    query = Appointment.query.filter(Appointment.patient_id != 999)
    
    if filter_type == 'all':
        query = query.filter(Appointment.status.in_(['Booked', 'Completed']))
    elif filter_type == 'upcoming':
        query = query.filter(
            Appointment.status == 'Booked',
            Appointment.appointment_date >= today
        )
    elif filter_type == 'past':
        query = query.filter(Appointment.status == 'Completed')
    elif filter_type == 'booked':
        query = query.filter(Appointment.status == 'Booked')
    elif filter_type == 'cancelled':
        query = query.filter(Appointment.status == 'Cancelled')
    elif filter_type == 'absent':
        query = query.filter(Appointment.status == 'Absent')
    
    appointments = query.order_by(Appointment.appointment_date.desc()).all()
    patients = Patient.query.all()
    doctors = Doctor.query.all()
    
    return render_template('admin_manage_appointments.html', 
                        admin=admin, 
                        appointments=appointments,
                        patients=patients,
                        doctors=doctors,
                        filter_type=filter_type)

# BOOK APPOINTMENT
@app.route('/admin/appointment/book', methods=['POST'])
@login_required
def admin_book_appointment():
    if current_user.user_role != 1:
        return redirect(url_for('home'))
    
    patient_id = request.form.get('patient_id')
    doctor_id = request.form.get('doctor_id')
    appointment_date = request.form.get('appointment_date')
    appointment_time = request.form.get('appointment_time')
    reason = request.form.get('reason')
    
    if not all([patient_id, doctor_id, appointment_date, appointment_time]):
        flash("All fields are required", "error")
        return redirect(url_for('admin_manage_appointments'))
    

    try:
        appointment_date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
    except:
        flash("Invalid date format", "error")
        return redirect(url_for('admin_manage_appointments'))
    
    existing = Appointment.query.filter_by(
        doctor_id=doctor_id,
        appointment_date=appointment_date_obj,
        appointment_time=appointment_time,
        status='Booked'
    ).first()
    
    if existing:
        flash("This time slot is already booked for the doctor. Please choose another time.", "error")
        return redirect(url_for('admin_manage_appointments'))
    
    appointment = Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        appointment_date=appointment_date_obj,
        appointment_time=appointment_time,
        status='Booked',
        reason=reason
    )
    db.session.add(appointment)
    db.session.commit()
    
    flash("Appointment booked successfully", "success")
    return redirect(url_for('admin_manage_appointments'))

# UPDATE APPOINTMENT
@app.route('/admin/appointment/<int:appointment_id>/update', methods=['GET', 'POST'])
@login_required
def admin_update_appointment(appointment_id):
    if current_user.user_role != 1:
        return redirect(url_for('home'))
    
    admin = Admin.query.filter_by(admin_id=current_user.id).first()
    appointment = Appointment.query.get_or_404(appointment_id)
    patients = Patient.query.all()
    doctors = Doctor.query.all()
    
    if request.method == 'POST':
        appointment_date = request.form.get('appointment_date')
        appointment_time = request.form.get('appointment_time')
        reason = request.form.get('reason')
        status = request.form.get('status')
        
        try:
            appointment_date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
        except:
            flash("Invalid date format", "error")
            return render_template('admin_update_appointment.html',
                                admin=admin,
                                appointment=appointment,
                                patients=patients,
                                doctors=doctors)
        
        # Check for conflicts
        existing = Appointment.query.filter(
            Appointment.doctor_id == appointment.doctor_id,
            Appointment.appointment_date == appointment_date_obj,
            Appointment.appointment_time == appointment_time,
            Appointment.status == 'Booked',
            Appointment.id != appointment_id
        ).first()
        
        if existing:
            flash("This time slot is already booked for the doctor.", "error")
            return render_template('admin_update_appointment.html',
                                admin=admin,
                                appointment=appointment,
                                patients=patients,
                                doctors=doctors)
        
        appointment.appointment_date = appointment_date_obj
        appointment.appointment_time = appointment_time
        appointment.reason = reason
        appointment.status = status
        
        db.session.commit()
        flash("Appointment updated successfully", "success")
        return redirect(url_for('admin_manage_appointments'))
    
    return render_template('admin_update_appointment.html',
                        admin=admin,
                        appointment=appointment,
                        patients=patients,
                        doctors=doctors)

@app.route('/admin/appointment/<int:appointment_id>/status', methods=['POST'])
@login_required
def admin_update_appointment_status(appointment_id):
    if current_user.user_role != 1:
        return redirect(url_for('home'))
    
    appointment = Appointment.query.get_or_404(appointment_id)
    new_status = request.form.get('status')
    
    if new_status in ['Completed', 'Cancelled', 'Booked']:
        appointment.status = new_status
        db.session.commit()
        flash(f"Appointment status updated to {new_status}", "success")
    
    return redirect(url_for('admin_manage_appointments'))

@app.route('/admin/appointment/<int:appointment_id>/delete', methods=['POST'])
@login_required
def admin_delete_appointment(appointment_id):
    if current_user.user_role != 1:
        return redirect(url_for('home'))
    
    appointment = Appointment.query.get_or_404(appointment_id)
    
    Treatment.query.filter_by(appointment_id=appointment_id).delete()
    
    db.session.delete(appointment)
    db.session.commit()
    
    flash("Appointment deleted successfully", "success")
    return redirect(url_for('admin_manage_appointments'))

# ==================== ADMIN - SEARCH & HISTORY ROUTES ====================

# SEARCH DOCTORS BY NAME OR SPECIALIZATION
@app.route('/admin/search/doctors', methods=['GET'])
@login_required
def admin_search_doctors():
    if current_user.user_role != 1:
        return redirect(url_for('home'))
    
    admin = Admin.query.filter_by(admin_id=current_user.id).first()
    
    search_query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'name')
    
    if search_query:
        if search_type == 'specialization':
            doctors = Doctor.query.filter(
                Doctor.specialization.ilike(f'%{search_query}%')
            ).all()
        else:  # search by name
            doctors = Doctor.query.filter(
                Doctor.full_name.ilike(f'%{search_query}%')
            ).all()
    else:
        doctors = Doctor.query.all()
    
    return render_template('admin_search_doctors.html',
                        admin=admin,
                        doctors=doctors,
                        search_query=search_query,
                        search_type=search_type)

# SEARCH PATIENTS BY NAME, ID, OR CONTACT
@app.route('/admin/search/patients', methods=['GET'])
@login_required
def admin_search_patients():
    if current_user.user_role != 1:
        return redirect(url_for('home'))
    
    admin = Admin.query.filter_by(admin_id=current_user.id).first()
    
    search_query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'name')
    
    if search_query:
        if search_type == 'id':
            try:
                patients = Patient.query.filter(
                    or_(
                        Patient.id == int(search_query),
                        Patient.patient_id == int(search_query)
                    )
                ).all()
            except ValueError:
                patients = []
        elif search_type == 'contact':
            patients = Patient.query.filter(
                db.or_(
                    Patient.phone.ilike(f'%{search_query}%'),
                    Patient.email.ilike(f'%{search_query}%')
                )
            ).all()
        else:
            patients = Patient.query.filter(
                Patient.full_name.ilike(f'%{search_query}%')
            ).all()
    else:
        patients = Patient.query.all()
    
    return render_template('admin_search_patients.html',
                        admin=admin,
                        patients=patients,
                        search_query=search_query,
                        search_type=search_type)

# VIEW COMPLETE PATIENT HISTORY
@app.route('/admin/patient/<int:patient_id>/history')
@login_required
def admin_patient_history(patient_id):
    if current_user.user_role != 1:
        return redirect(url_for('home'))
    
    admin = Admin.query.filter_by(admin_id=current_user.id).first()
    patient = _get_patient_by_identifier_or_404(patient_id)
    
    patient_appt_filter = or_(
        Appointment.patient_id == patient.id,
        Appointment.patient_id == patient.patient_id
    )
    appointments = Appointment.query.filter(
        patient_appt_filter
    ).order_by(Appointment.appointment_date.desc()).all()
    
    treatments = Treatment.query.join(Appointment).filter(
        patient_appt_filter
    ).order_by(Treatment.created_at.desc()).all()
    
    total_appointments = len(appointments)
    completed_count = sum(1 for apt in appointments if apt.status == 'Completed')
    cancelled_count = sum(1 for apt in appointments if apt.status == 'Cancelled')
    booked_count = sum(1 for apt in appointments if apt.status == 'Booked')
    
    return render_template('admin_patient_history.html',
                        admin=admin,
                        patient=patient,
                        appointments=appointments,
                        treatments=treatments,
                        total_appointments=total_appointments,
                        completed_count=completed_count,
                        cancelled_count=cancelled_count,
                        booked_count=booked_count)

# VIEW ALL TREATMENTS SYSTEM-WIDE
@app.route('/admin/treatments')
@login_required
def admin_view_treatments():
    if current_user.user_role != 1:
        return redirect(url_for('home'))
    
    admin = Admin.query.filter_by(admin_id=current_user.id).first()
    
    treatments = Treatment.query.join(Appointment).order_by(
        Treatment.created_at.desc()
    ).all()
    
    total_treatments = len(treatments)
    
    return render_template('admin_view_treatments.html',
                        admin=admin,
                        treatments=treatments,
                        total_treatments=total_treatments)

@app.route('/admin/patient/<int:patient_id>/treatments')
@login_required
def admin_patient_treatments(patient_id):
    if current_user.user_role != 1:
        return redirect(url_for('home'))
    
    admin = Admin.query.filter_by(admin_id=current_user.id).first()
    patient = _get_patient_by_identifier_or_404(patient_id)
    
    patient_appt_filter = or_(
        Appointment.patient_id == patient.id,
        Appointment.patient_id == patient.patient_id
    )
    treatments = Treatment.query.join(Appointment).filter(
        patient_appt_filter
    ).order_by(Treatment.created_at.desc()).all()
    
    total_treatments = len(treatments)
    
    return render_template('admin_patient_treatments.html',
                        admin=admin,
                        patient=patient,
                        treatments=treatments,
                        total_treatments=total_treatments)

@app.route('/admin/doctor/<int:doctor_id>/appointments')
@login_required
def admin_doctor_appointments(doctor_id):
    if current_user.user_role != 1:
        return redirect(url_for('home'))
    
    admin = Admin.query.filter_by(admin_id=current_user.id).first()
    doctor = _get_doctor_by_identifier_or_404(doctor_id)
    
    appointments = Appointment.query.filter(
        or_(
            Appointment.doctor_id == doctor.id,
            Appointment.doctor_id == doctor.doctor_id
        )
    ).order_by(Appointment.appointment_date.desc()).all()
    
    total_count = len(appointments)
    booked_count = sum(1 for apt in appointments if apt.status == 'Booked')
    completed_count = sum(1 for apt in appointments if apt.status == 'Completed')
    cancelled_count = sum(1 for apt in appointments if apt.status == 'Cancelled')
    
    return render_template('admin_doctor_appointments.html',
                        admin=admin,
                        doctor=doctor,
                        appointments=appointments,
                        total_count=total_count,
                        booked_count=booked_count,
                        completed_count=completed_count,
                        cancelled_count=cancelled_count)

# ==================== DOCTOR ROUTES ====================

# DOCTOR LOGIN
@app.route('/doctor/login', methods=['GET', 'POST'])
def doctor_login():
    if request.method == 'POST':
        identifier = request.form.get('username') or request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter(
            db.and_(
                User.user_role == 2,
                db.or_(User.username == identifier, User.email == identifier)
            )
        ).first()
        
        if user and user.password and user.password == password:
            doctor = Doctor.query.filter_by(doctor_id=user.id).first()
            if doctor and doctor.flagged:
                return render_template('doctor_login.html', error="Your account has been blacklisted. Please contact administration.")
            login_user(user)
            return redirect(url_for('doctor_dashboard'))
        return render_template('doctor_login.html', error="Invalid credentials")
    
    return render_template('doctor_login.html')

# DOCTOR DASHBOARD
@app.route('/doctor/dashboard')
@login_required
def doctor_dashboard():
    if current_user.user_role != 2:
        return redirect(url_for('home'))
    
    doctor = Doctor.query.filter_by(doctor_id=current_user.id).first()
    
    doctor_appt_filter = or_(
        Appointment.doctor_id == doctor.id,
        Appointment.doctor_id == doctor.doctor_id
    )
    
    today = datetime.now().date()
    today_appointments = Appointment.query.filter(
        doctor_appt_filter,
        Appointment.appointment_date == today,
        Appointment.patient_id != 999
    ).all()

    week_end = today + timedelta(days=7)
    week_appointments = Appointment.query.filter(
        doctor_appt_filter,
        Appointment.appointment_date >= today,
        Appointment.appointment_date <= week_end,
        Appointment.status == 'Booked'
    ).order_by(Appointment.appointment_date, Appointment.appointment_time).all()
    
    total_appointments = Appointment.query.filter(
        doctor_appt_filter,
        Appointment.patient_id != 999
    ).count()
    booked_appointments = Appointment.query.filter(
        doctor_appt_filter,
        Appointment.status == 'Booked'
    ).count()
    completed_appointments = Appointment.query.filter(
        doctor_appt_filter,
        Appointment.status == 'Completed'
    ).count()
    
    total_patients = db.session.query(Appointment.patient_id).filter(
        doctor_appt_filter,
        Appointment.patient_id != 999
    ).distinct().count()

    patient_ids = db.session.query(Appointment.patient_id).filter(
        doctor_appt_filter,
        Appointment.patient_id != 999
    ).distinct().all()
    patients = []
    for (pid,) in patient_ids:
        patient = Patient.query.get(pid)
        if patient:
            patients.append(patient)
    
    return render_template('doctor_dashboard.html',
                        doctor=doctor,
                        today_appointments=today_appointments,
                        week_appointments=week_appointments,
                        total_appointments=total_appointments,
                        booked_appointments=booked_appointments,
                        completed_appointments=completed_appointments,
                        pending_appointments=booked_appointments,
                        total_patients=total_patients,
                        patients=patients)

# DOCTOR LOGOUT
@app.route('/doctor/logout')
@login_required
def doctor_logout():
    logout_user()
    return redirect(url_for('home'))

# DOCTOR VIEW APPOINTMENTS
@app.route('/doctor/appointments')
@login_required
def doctor_appointments():
    if current_user.user_role != 2:
        return redirect(url_for('home'))
    
    doctor = Doctor.query.filter_by(doctor_id=current_user.id).first()
    filter_status = request.args.get('status', 'all')
    
    doctor_appt_filter = or_(
        Appointment.doctor_id == doctor.id,
        Appointment.doctor_id == doctor.doctor_id
    )
    query = Appointment.query.filter(
        doctor_appt_filter,
        Appointment.status != 'Available'  
    )
    
    if filter_status != 'all':
        query = query.filter(Appointment.status == filter_status.capitalize())
    
    appointments = query.order_by(Appointment.appointment_date.desc()).all()
    
    return render_template('doctor_appointments.html', 
                        doctor=doctor, 
                        appointments=appointments,
                        filter_status=filter_status)

# DOCTOR UPDATE APPOINTMENT STATUS
@app.route('/doctor/appointment/<int:appointment_id>/status', methods=['POST'])
@login_required
def doctor_update_appointment_status(appointment_id):
    if current_user.user_role != 2:
        return redirect(url_for('home'))
    
    appointment = Appointment.query.get_or_404(appointment_id)
    doctor = Doctor.query.filter_by(doctor_id=current_user.id).first()
    
    if appointment.doctor_id not in (doctor.id, doctor.doctor_id):
        flash("Unauthorized access", "error")
        return redirect(url_for('doctor_appointments'))
    
    new_status = request.form.get('status')
    
    if new_status == 'Completed':
        appointment.status = new_status
        db.session.commit()
        flash(f"Appointment marked as completed", "success")
    elif new_status == 'Absent':
        appointment.status = 'Absent'
        
        next_day = appointment.appointment_date + timedelta(days=1)
        
        while next_day.weekday() >= 5:
            next_day += timedelta(days=1)
        
        existing_slot = Appointment.query.filter(
            or_(
                Appointment.doctor_id == doctor.id,
                Appointment.doctor_id == doctor.doctor_id
            ),
            Appointment.appointment_date == next_day,
            Appointment.appointment_time == appointment.appointment_time
        ).first()
        
        if not existing_slot:
            rescheduled = Appointment(
                doctor_id=appointment.doctor_id,
                patient_id=appointment.patient_id,
                appointment_date=next_day,
                appointment_time=appointment.appointment_time,
                status='Booked',
                reason=appointment.reason
            )
            db.session.add(rescheduled)
            db.session.commit()
            flash(f"Appointment marked as absent and rescheduled to {next_day.strftime('%B %d, %Y')} at {appointment.appointment_time}", "success")
        else:
            db.session.commit()
            flash(f"Appointment marked as absent. Could not reschedule - slot on {next_day.strftime('%B %d, %Y')} is already taken.", "warning")
    elif new_status == 'Cancelled':
        appointment.status = new_status
        db.session.commit()
        flash(f"Appointment cancelled", "success")
    
    return redirect(url_for('doctor_appointments'))

# DOCTOR ADD/UPDATE TREATMENT
@app.route('/doctor/appointment/<int:appointment_id>/treatment', methods=['GET', 'POST'])
@login_required
def doctor_add_treatment(appointment_id):
    if current_user.user_role != 2:
        return redirect(url_for('home'))
    
    doctor = Doctor.query.filter_by(doctor_id=current_user.id).first()
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.doctor_id not in (doctor.id, doctor.doctor_id):
        flash("Unauthorized access", "error")
        return redirect(url_for('doctor_appointments'))
    
    if appointment.status != 'Completed':
        flash("Treatment can only be added to completed appointments. Please mark the appointment as completed first.", "error")
        return redirect(url_for('doctor_appointments'))

    existing_treatment = Treatment.query.filter_by(appointment_id=appointment_id).first()
    
    if request.method == 'POST':
        diagnosis = request.form.get('diagnosis')
        prescription = request.form.get('prescription')
        notes = request.form.get('notes')
        
        if not diagnosis:
            flash("Diagnosis is required", "error")
            return render_template('doctor_add_treatment.html',
                                doctor=doctor,
                                appointment=appointment,
                                treatment=existing_treatment)
        
        if existing_treatment:
            existing_treatment.diagnosis = diagnosis
            existing_treatment.prescription = prescription
            existing_treatment.notes = notes
            flash("Treatment updated successfully", "success")
        else:
            treatment = Treatment(
                appointment_id=appointment_id,
                diagnosis=diagnosis,
                prescription=prescription,
                notes=notes,
                created_at=datetime.now()
            )
            db.session.add(treatment)
            flash("Treatment added successfully", "success")
        
        db.session.commit()
        
        return redirect(url_for('doctor_view_patient', patient_id=appointment.patient_id))
    
    return render_template('doctor_add_treatment.html',
                        doctor=doctor,
                        appointment=appointment,
                        treatment=existing_treatment)

# DOCTOR VIEW PATIENT FULL HISTORY
@app.route('/doctor/patient/<int:patient_id>')
@login_required
def doctor_view_patient(patient_id):
    if current_user.user_role != 2:
        return redirect(url_for('home'))
    
    doctor = Doctor.query.filter_by(doctor_id=current_user.id).first()
    patient = _get_patient_by_identifier_or_404(patient_id)
    
    doctor_match = or_(
        Appointment.doctor_id == doctor.id,
        Appointment.doctor_id == doctor.doctor_id
    )
    patient_match = or_(
        Appointment.patient_id == patient.id,
        Appointment.patient_id == patient.patient_id
    )
    appointments = Appointment.query.filter(
        doctor_match,
        patient_match
    ).order_by(Appointment.appointment_date.desc()).all()
    
    treatments = Treatment.query.join(Appointment).filter(
        doctor_match,
        patient_match
    ).order_by(Treatment.created_at.desc()).all()
    
    treatment_count = len(treatments)
    
    return render_template('doctor_view_patient.html',
                        doctor=doctor,
                        patient=patient,
                        appointments=appointments,
                        treatments=treatments,
                        treatment_count=treatment_count)

# DOCTOR VIEW ALL PATIENTS
@app.route('/doctor/patients')
@login_required
def doctor_patients():
    if current_user.user_role != 2:
        return redirect(url_for('home'))
    
    doctor = Doctor.query.filter_by(doctor_id=current_user.id).first()
    
    doctor_appt_filter = or_(
        Appointment.doctor_id == doctor.id,
        Appointment.doctor_id == doctor.doctor_id
    )
    patient_ids = db.session.query(Appointment.patient_id).filter(
        doctor_appt_filter,
        Appointment.patient_id != 999
    ).distinct().all()
    
    patients = []
    for (pid,) in patient_ids:
        patient = Patient.query.get(pid)
        if patient:
            patients.append(patient)
    
    return render_template('doctor_patients.html',
                        doctor=doctor,
                        patients=patients)

# DOCTOR AVAILABILITY
@app.route('/doctor/availability', methods=['GET', 'POST'])
@login_required
def doctor_availability():
    if current_user.user_role != 2:
        return redirect(url_for('home'))
    
    doctor = Doctor.query.filter_by(doctor_id=current_user.id).first()
    
    if request.method == 'POST':
        today = datetime.now().date()
        Appointment.query.filter(
            or_(
                Appointment.doctor_id == doctor.id,
                Appointment.doctor_id == doctor.doctor_id
            ),
            Appointment.appointment_date >= today,
            Appointment.status == 'Available'
        ).delete(synchronize_session=False)
        
        time_slots = ['10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00']
        
        for i in range(7):
            day_enabled = request.form.get(f'day_{i}')
            if day_enabled == 'on':
                date = today + timedelta(days=i)
                
                selected_slots = request.form.getlist(f'slots_{i}')
                
                for time_slot in selected_slots:
                    if time_slot in time_slots:
                        existing = Appointment.query.filter(
                            or_(
                                Appointment.doctor_id == doctor.id,
                                Appointment.doctor_id == doctor.doctor_id
                            ),
                            Appointment.appointment_date == date,
                            Appointment.appointment_time == time_slot
                        ).first()
                        
                        if not existing:
                            slot = Appointment(
                                doctor_id=doctor.id,
                                appointment_date=date,
                                appointment_time=time_slot,
                                status='Available',
                                patient_id=999
                            )
                            db.session.add(slot)
                        elif existing.status == 'Cancelled' or existing.status == 'Absent':
                            existing.status = 'Available'
                            existing.patient_id = 999
                            existing.reason = None
        
        db.session.commit()
        flash("Availability settings saved successfully!", "success")
        return redirect(url_for('doctor_dashboard'))
    
    today = datetime.now().date()
    availability_data = []
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    time_slots = ['10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00']
    
    for i in range(7):
        date = today + timedelta(days=i)
        day_name = day_names[date.weekday()]
        
        existing_slots = Appointment.query.filter(
            or_(
                Appointment.doctor_id == doctor.id,
                Appointment.doctor_id == doctor.doctor_id
            ),
            Appointment.appointment_date == date,
            Appointment.status == 'Available'
        ).all()
        
        existing_times = [slot.appointment_time for slot in existing_slots]
        
        availability_data.append({
            'day_name': day_name,
            'date': date,
            'existing_times': existing_times,
            'is_weekend': False
        })
    
    return render_template('doctor_availability.html', 
                        doctor=doctor,
                        availability_data=availability_data,
                        time_slots=time_slots)

# ==================== PATIENT ROUTES ====================

# PATIENT LOGIN
@app.route('/patient/login', methods=['GET', 'POST'])
def patient_login():
    if request.method == 'POST':
        identifier = request.form.get('username') or request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter(
            db.and_(
                User.user_role == 3,
                db.or_(User.username == identifier, User.email == identifier)
            )
        ).first()
        
        if user and user.password and user.password == password:
            patient = Patient.query.filter_by(patient_id=user.id).first()
            if patient and patient.flagged:
                return render_template('patient_login.html', error="Your account has been blacklisted. Please contact administration.")
            login_user(user)
            return redirect(url_for('patient_dashboard'))
        return render_template('patient_login.html', error="Invalid credentials")
    
    return render_template('patient_login.html')

# PATIENT REGISTER
@app.route('/patient/register', methods=['GET', 'POST'])
def patient_register():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        username = request.form.get('username') or (request.form.get('email') or '').split('@')[0]
        email = request.form.get('email')
        password = request.form.get('password')
        phone = request.form.get('phone')
        date_of_birth = request.form.get('date_of_birth')
        gender = request.form.get('gender')
        blood_group = request.form.get('blood_group')
        address = request.form.get('address')
        
        if not all([full_name, email, password]):
            return render_template('patient_register.html', 
                                error="Name, email and password are required")
        
        if User.query.filter_by(email=email).first():
            return render_template('patient_register.html', 
                                error="Email already registered")
        if User.query.filter_by(username=username).first():
            return render_template('patient_register.html',
                                error="Username already taken")
        
        user = User(
            username=username, 
            email=email,
            password=password,
            user_role=3
        )
        db.session.add(user)
        db.session.flush()
        

        dob = None
        if date_of_birth:
            try:
                dob = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
            except:
                pass
        

        patient = Patient(
            patient_id=user.id,
            full_name=full_name,
            username=user.username,
            email=email,
            password=user.password,
            phone=phone,
            date_of_birth=dob,
            gender=gender,
            blood_group=blood_group,
            address=address
        )
        db.session.add(patient)
        db.session.commit()
        
        flash("Registration successful! Please login.", "success")
        return redirect(url_for('patient_login'))
    
    return render_template('patient_register.html')

# PATIENT DASHBOARD
@app.route('/patient/dashboard')
@login_required
def patient_dashboard():
    if current_user.user_role != 3:
        return redirect(url_for('home'))
    
    patient = Patient.query.filter_by(patient_id=current_user.id).first()
    
    patient_appt_filter = or_(
        Appointment.patient_id == patient.id,
        Appointment.patient_id == patient.patient_id
    )
    

    today = datetime.now().date()
    upcoming_appointments = Appointment.query.filter(
        patient_appt_filter,
        Appointment.appointment_date >= today,
        Appointment.status == 'Booked'
    ).order_by(Appointment.appointment_date).all()
    
    past_appointments = Appointment.query.filter(
        patient_appt_filter,
        Appointment.appointment_date < today
    ).order_by(Appointment.appointment_date.desc()).limit(5).all()
    
    total_appointments = Appointment.query.filter(patient_appt_filter).count()
    completed_appointments = Appointment.query.filter(
        patient_appt_filter,
        Appointment.status == 'Completed'
    ).count()
    upcoming_count = len(upcoming_appointments)
    departments = Department.query.all()
    
    return render_template('patient_dashboard.html',
                        patient=patient,
                        upcoming_appointments=upcoming_appointments,
                        past_appointments=past_appointments,
                        total_appointments=total_appointments,
                        completed_count=completed_appointments,
                        upcoming_count=upcoming_count,
                        departments=departments)



#PATIENT LOGOUT
@app.route('/patient/logout')
@login_required
def patient_logout():
    logout_user()
    return redirect(url_for('home'))



@app.route('/patient/departments')
@login_required
def patient_departments():
    if current_user.user_role != 3:
        return redirect(url_for('home'))
    
    patient = Patient.query.filter_by(patient_id=current_user.id).first()
    departments = Department.query.all()
    
    return render_template('patient_departments.html', 
                        patient=patient, 
                        departments=departments)

@app.route('/patient/department/<int:dept_id>/doctors')
@login_required
def patient_view_doctors(dept_id):
    if current_user.user_role != 3:
        return redirect(url_for('home'))
    
    patient = Patient.query.filter_by(patient_id=current_user.id).first()
    department = Department.query.get_or_404(dept_id)
    # Exclude blacklisted doctors from patient view
    doctors = Doctor.query.filter_by(department_id=dept_id, flagged=False).all()
    
    return render_template('patient_view_doctors.html',
                        patient=patient,
                        department=department,
                        doctors=doctors)

# PATIENT VIEW DOCTOR PROFILE
@app.route('/patient/doctor/<int:doctor_id>/profile')
@login_required
def patient_doctor_profile(doctor_id):
    if current_user.user_role != 3:
        return redirect(url_for('home'))
    
    patient = Patient.query.filter_by(patient_id=current_user.id).first()
    doctor = _get_doctor_by_identifier_or_404(doctor_id)
    
    return render_template('patient_doctor_profile.html', 
                        patient=patient, 
                        doctor=doctor)


@app.route('/patient/doctor/<int:doctor_id>/view-profile')
@login_required
def patient_view_doctor_profile(doctor_id):
    if current_user.user_role != 3:
        return redirect(url_for('home'))
    
    patient = Patient.query.filter_by(patient_id=current_user.id).first()
    doctor = _get_doctor_by_identifier_or_404(doctor_id)
    
    return render_template('patient_doctor_profile.html', 
                        patient=patient, 
                        doctor=doctor)

# PATIENT BOOK APPOINTMENT
@app.route('/patient/book/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
def patient_book_appointment(doctor_id):
    if current_user.user_role != 3:
        return redirect(url_for('home'))

    patient = Patient.query.filter_by(patient_id=current_user.id).first()
    doctor = _get_doctor_by_identifier_or_404(doctor_id)
    
    if doctor.flagged:
        flash("This doctor is currently unavailable for appointments.", "error")
        return redirect(url_for('patient_departments'))

    #(next 7 days)
    today = datetime.now().date()
    end_date = today + timedelta(days=7)
    
    available_slots = Appointment.query.filter(
        or_(
            Appointment.doctor_id == doctor.id,
            Appointment.doctor_id == doctor.doctor_id
        ),
        Appointment.status == 'Available',
        Appointment.appointment_date >= today,
        Appointment.appointment_date <= end_date
    ).order_by(Appointment.appointment_date, Appointment.appointment_time).all()
    
    slots_by_date = {}
    for slot in available_slots:
        date_str = slot.appointment_date.strftime('%Y-%m-%d')
        if date_str not in slots_by_date:
            slots_by_date[date_str] = []
        slots_by_date[date_str].append(slot)

    if request.method == 'POST':
        appointment_date = request.form.get('appointment_date')
        appointment_time = request.form.get('appointment_time')
        reason = request.form.get('reason')

        if not all([appointment_date, appointment_time]):
            return render_template('patient_book_appointment.html',
                                error="Please select date and time",
                                patient=patient,
                                doctor=doctor,
                                available_slots=available_slots,
                                slots_by_date=slots_by_date)

        try:
            appointment_date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
        except:
            return render_template('patient_book_appointment.html',
                                error="Invalid date format",
                                patient=patient,
                                doctor=doctor,
                                available_slots=available_slots,
                                slots_by_date=slots_by_date)
        
        slot_to_book = Appointment.query.filter(
            or_(
                Appointment.doctor_id == doctor.id,
                Appointment.doctor_id == doctor.doctor_id
            ),
            Appointment.appointment_date == appointment_date_obj,
            Appointment.appointment_time == appointment_time,
            Appointment.status == 'Available'
        ).first()

        if not slot_to_book:
            return render_template('patient_book_appointment.html',
                                error="This time slot is no longer available. Please choose another time.",
                                patient=patient,
                                doctor=doctor,
                                available_slots=available_slots,
                                slots_by_date=slots_by_date)

        slot_to_book.patient_id = patient.id
        slot_to_book.status = 'Booked'
        slot_to_book.reason = reason
        db.session.commit()

        flash("Appointment booked successfully!", "success")
        return redirect(url_for('patient_my_appointments'))

    return render_template('patient_book_appointment.html',
                        patient=patient,
                        doctor=doctor,
                        available_slots=available_slots,
                        slots_by_date=slots_by_date)

# PATIENT VIEW MY APPOINTMENTS
@app.route('/patient/appointments')
@login_required
def patient_my_appointments():
    if current_user.user_role != 3:
        return redirect(url_for('home'))
    
    patient = Patient.query.filter_by(patient_id=current_user.id).first()
    filter_status = request.args.get('status', 'all')
    
    patient_appt_filter = or_(
        Appointment.patient_id == patient.id,
        Appointment.patient_id == patient.patient_id
    )
    query = Appointment.query.filter(patient_appt_filter)
    
    today = datetime.now().date()
    if filter_status == 'upcoming':
        query = query.filter(Appointment.appointment_date >= today, Appointment.status == 'Booked')
    elif filter_status == 'past':
        query = query.filter(Appointment.appointment_date < today)
    elif filter_status == 'completed':
        query = query.filter(Appointment.status == 'Completed')
    elif filter_status == 'cancelled':
        query = query.filter(Appointment.status == 'Cancelled')
    
    appointments = query.order_by(Appointment.appointment_date.desc()).all()
    
    return render_template('patient_my_appointments.html', 
                        patient=patient, 
                        appointments=appointments,
                        filter_status=filter_status)


@app.route('/patient/appointment/<int:appointment_id>')
@login_required
def patient_appointment_details(appointment_id):
    if current_user.user_role != 3:
        return redirect(url_for('home'))
    
    patient = Patient.query.filter_by(patient_id=current_user.id).first()
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.patient_id not in (patient.id, patient.patient_id):
        flash("Unauthorized access", "error")
        return redirect(url_for('patient_my_appointments'))
    
    treatment = Treatment.query.filter_by(appointment_id=appointment_id).first()
    
    return render_template('patient_appointment_details.html',
                        patient=patient,
                        appointment=appointment,
                        treatment=treatment)

@app.route('/patient/appointment/<int:appointment_id>/view')
@login_required
def patient_view_appointment_details(appointment_id):
    if current_user.user_role != 3:
        return redirect(url_for('home'))
    
    patient = Patient.query.filter_by(patient_id=current_user.id).first()
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.patient_id not in (patient.id, patient.patient_id):
        flash("Unauthorized access", "error")
        return redirect(url_for('patient_my_appointments'))
    
    treatment = Treatment.query.filter_by(appointment_id=appointment_id).first()
    
    return render_template('patient_appointment_details.html',
                        patient=patient,
                        appointment=appointment,
                        treatment=treatment)

@app.route('/patient/appointment/<int:appointment_id>/cancel', methods=['GET', 'POST'])
@login_required
def patient_cancel_appointment(appointment_id):
    if current_user.user_role != 3:
        return redirect(url_for('home'))
    
    patient = Patient.query.filter_by(patient_id=current_user.id).first()
    appointment = Appointment.query.get_or_404(appointment_id)
    
    if appointment.patient_id not in (patient.id, patient.patient_id):
        flash("Unauthorized access", "error")
        return redirect(url_for('patient_my_appointments'))
    
    if appointment.status != 'Booked':
        flash("Only booked appointments can be cancelled", "error")
        return redirect(url_for('patient_my_appointments'))
    
    appointment.status = 'Available'
    appointment.patient_id = 999 
    appointment.reason = None
    db.session.commit()
    
    flash("Appointment cancelled successfully. The slot is now available for other patients.", "success")
    return redirect(url_for('patient_my_appointments'))

# PATIENT VIEW TREATMENT HISTORY
@app.route('/patient/treatments')
@login_required
def patient_treatment_history():
    if current_user.user_role != 3:
        return redirect(url_for('home'))

    patient = Patient.query.filter_by(patient_id=current_user.id).first()

    patient_appt_filter = or_(
        Appointment.patient_id == patient.id,
        Appointment.patient_id == patient.patient_id
    )
    treatments = Treatment.query.join(Appointment).filter(
        patient_appt_filter
    ).order_by(Treatment.created_at.desc()).all()

    return render_template('patient_treatment_history.html',
                        patient=patient,
                        treatments=treatments)

# PATIENT SEARCH DOCTORS
@app.route('/patient/search/doctors', methods=['GET'])
@login_required
def patient_search_doctors():
    if current_user.user_role != 3:
        return redirect(url_for('home'))
    
    patient = Patient.query.filter_by(patient_id=current_user.id).first()
    
    search_query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'name')
    
    if search_query:
        if search_type == 'specialization':
            doctors = Doctor.query.filter(
                Doctor.specialization.ilike(f'%{search_query}%'),
                Doctor.flagged == False
            ).all()
        else:
            doctors = Doctor.query.filter(
                Doctor.full_name.ilike(f'%{search_query}%'),
                Doctor.flagged == False
            ).all()
    else:
        doctors = Doctor.query.filter_by(flagged=False).all()
    
    return render_template('patient_search_doctors.html',
                        patient=patient,
                        doctors=doctors,
                        search_query=search_query,
                        search_type=search_type)

# PATIENT EDIT PROFILE
@app.route('/patient/profile/edit', methods=['GET', 'POST'])
@login_required
def patient_edit_profile():
    if current_user.user_role != 3:
        return redirect(url_for('home'))
    
    patient = Patient.query.filter_by(patient_id=current_user.id).first()
    
    if request.method == 'POST':
        new_username = request.form.get('username')
        patient.full_name = request.form.get('full_name')
        patient.phone = request.form.get('phone')
        patient.address = request.form.get('address')
        patient.blood_group = request.form.get('blood_group')
        patient.gender = request.form.get('gender')
        
        date_of_birth = request.form.get('date_of_birth')
        if date_of_birth:
            try:
                patient.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
            except:
                pass
        
        user = User.query.get(patient.patient_id)
        if user and new_username and new_username != user.username:
            existing_user = User.query.filter_by(username=new_username).first()
            if existing_user:
                flash("Username already exists. Please choose another.", "error")
                return redirect(url_for('patient_edit_profile'))
            user.username = new_username
            patient.username = new_username
        
        db.session.commit()
        flash("Profile updated successfully", "success")
        return redirect(url_for('patient_dashboard'))
    
    return render_template('patient_edit_profile.html', patient=patient)

# ==================== GENERAL LOGOUT ====================

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))
