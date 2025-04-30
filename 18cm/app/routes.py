from flask import render_template, redirect, url_for, jsonify, request, session, current_app, flash
from app import app, db
from app.models import Appointment, MedicalRecord, Diagnosis, Medication
from datetime import datetime, timedelta
import json
import os
from functools import wraps
import hl7

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def load_clinics_data():
    json_path = os.path.join(os.path.dirname(__file__), 'data', 'clinics.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

@app.route('/')
def index():
    # Only redirect to login if user is not logged in
    if 'user_id' not in session:
        return redirect(url_for('login'))
    # If user is logged in, show the index page
    return render_template('index.html')

@app.route('/home')
@login_required
def home():
    return render_template('index.html')

@app.route('/profile')
@login_required
def profile():
    try:
        # Get user data from users.json using the logged in user's ID
        app_root = current_app.root_path
        json_path = os.path.join(app_root, 'data', 'users.json')
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            user = data['users'][0]  # For now, just get first user
            
            # Format the user data for display
            formatted_user = {
                'enName': user['enName']['UnstructuredName'],
                'gender': 'Male' if user['gender'] == 'M' else 'Female',
                'idNo': f"{user['idNo']['Identification']}{user['idNo']['CheckDigit']}",
                'birthDate': f"{user['birthDate'][:4]}-{user['birthDate'][4:6]}-{user['birthDate'][6:]}"
            }
            
            return render_template('profile.html', user=formatted_user)
            
    except Exception as e:
        print(f"Error loading profile data: {e}")
        return redirect(url_for('home'))

@app.route('/clinics/<location>')
@login_required
def show_clinics(location):
    # Load clinics data from JSON
    clinics_data = load_clinics_data()
    
    # Map URL parameters to JSON keys
    location_map = {
        'hong_kong': 'HongKongIsland',
        'kowloon': 'Kowloon',
        'new_territories': 'NewTerritories'
    }
    
    # Get clinics for the selected location
    json_location = location_map.get(location, '')
    clinics_list = clinics_data.get(json_location, [])
    
    # Store the current location in session
    session['current_location'] = json_location
    
    # Transform data to match expected format
    formatted_clinics = [
        {
            'id': idx + 1,
            'name': clinic['District'],
            'quota': 5
        }
        for idx, clinic in enumerate(clinics_list)
    ]
    
    return render_template('clinics.html', clinics=formatted_clinics)

@app.route('/services/<int:clinic_id>')
@login_required
def select_service(clinic_id):
    # Load clinics data from JSON
    clinics_data = load_clinics_data()
    
    # Get the current location from session
    current_location = session.get('current_location')
    
    # Get clinics for the current location
    clinics_list = clinics_data.get(current_location, [])
    
    # Get the clinic using local index
    clinic_index = clinic_id - 1
    if clinic_index < len(clinics_list):
        selected_clinic = {
            'District': clinics_list[clinic_index]['District'],  # Store District with capital D
            'address': clinics_list[clinic_index]['Address'],
            'telephone': clinics_list[clinic_index]['Telephone']
        }
        session['selected_clinic'] = selected_clinic
    
    services = [
        {'id': 1, 'name': 'General Consultation'},
        {'id': 2, 'name': 'Acupuncture'}
    ]
    return render_template('services.html', services=services, clinic_id=clinic_id)

@app.route('/services/<int:clinic_id>/select/<int:service_id>')
@login_required
def set_service(clinic_id, service_id):
    services = {
        1: 'General Consultation',
        2: 'Acupuncture'
    }
    # Store service name in session
    session['selected_service'] = services.get(service_id)
    return redirect(url_for('select_timeslot', clinic_id=clinic_id, service_id=service_id))

@app.route('/timeslots/<int:clinic_id>/<int:service_id>')
@login_required
def select_timeslot(clinic_id, service_id):
    # Get today and tomorrow's dates
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    current_time = datetime.now().time()
    
    # Create timeslots structure with some slots marked as unavailable
    time_slots = ['09:00', '10:00', '11:00', '14:00', '15:00', '16:00']
    
    # Simulate some fully booked slots (in production this would come from database)
    fully_booked = {
        today.strftime('%Y-%m-%d'): ['11:00', '14:00'],  # These slots will be grey and disabled
        tomorrow.strftime('%Y-%m-%d'): ['10:00']  # This slot will be grey and disabled
    }
    
    available_slots = {
        today.strftime('%Y-%m-%d'): [],
        tomorrow.strftime('%Y-%m-%d'): []
    }
    
    # Add today's slots
    for time_str in time_slots:
        slot_time = datetime.strptime(time_str, '%H:%M').time()
        if slot_time > current_time:
            is_available = time_str not in fully_booked[today.strftime('%Y-%m-%d')]
            available_slots[today.strftime('%Y-%m-%d')].append({
                'id': len(time_slots) + 1,
                'time': time_str,
                'available': is_available
            })
    
    # Add tomorrow's slots
    for time_str in time_slots:
        is_available = time_str not in fully_booked[tomorrow.strftime('%Y-%m-%d')]
        available_slots[tomorrow.strftime('%Y-%m-%d')].append({
            'id': len(time_slots) + 1,
            'time': time_str,
            'available': is_available
        })
    
    # Handle timeslot selection
    if 'selected_timeslot' in request.args:
        selected_date = request.args.get('date')
        selected_time = request.args.get('time')
        if selected_date and selected_time:
            session['selected_timeslot'] = {
                'date': selected_date,
                'time': selected_time
            }
            return redirect(url_for('confirm_booking'))
    
    return render_template('timeslots.html', 
                         slots_by_date=available_slots,
                         clinic_id=clinic_id, 
                         service_id=service_id)

@app.route('/confirm', methods=['GET', 'POST'])
@login_required
def confirm_booking():
    if request.method == 'POST':
        # Create and save appointment
        new_appointment = Appointment(
            user_id=session['user_id'],
            clinic_name=session.get('selected_clinic', {}).get('District', ''),
            service_type=session.get('selected_service'),
            datetime=datetime.strptime(
                f"{session.get('selected_timeslot', {}).get('date')} {session.get('selected_timeslot', {}).get('time')}", 
                "%Y-%m-%d %H:%M"
            ),
            status='upcoming'
        )
        db.session.add(new_appointment)
        db.session.commit()
        
        # Clear booking session data
        session.pop('selected_clinic', None)
        session.pop('selected_service', None)
        session.pop('selected_timeslot', None)
        
        return redirect(url_for('booking_success'))

    # Show confirm page
    # Get user profile data
    profiles_path = os.path.join(current_app.root_path, 'data', 'profiles.json')
    with open(profiles_path, 'r', encoding='utf-8') as f:
        profiles = json.load(f)
        user_profile = next(
            (p for p in profiles['profiles'] if p['id'] == session['user_id']),
            None
        )

    booking = {
        'clinic': session.get('selected_clinic', {}),
        'service': session.get('selected_service'),
        'timeslot': session.get('selected_timeslot', {})
    }
    return render_template('confirm.html', 
                         booking=booking,
                         user=user_profile['personal_info'] if user_profile else None)

@app.route('/success')
@login_required
def booking_success():
    return render_template('success.html')

@app.route('/enquiry')
@login_required
def enquiry():
    appointments = Appointment.query.order_by(Appointment.datetime.desc()).all()
    return render_template('enquiry.html', appointments=appointments)

@app.route('/appointment/<int:appointment_id>')
@login_required
def appointment_detail(appointment_id):
    try:
        # Get appointment data
        appointment = Appointment.query.get_or_404(appointment_id)
        
        # Get clinic details
        clinics_data = load_clinics_data()
        clinic_details = None
        for region in clinics_data.values():
            for clinic in region:
                if clinic['District'] == appointment.clinic_name:
                    clinic_details = clinic
                    break
            if clinic_details:
                break

        # Get user profile
        profiles_path = os.path.join(current_app.root_path, 'data', 'profiles.json')
        with open(profiles_path, 'r', encoding='utf-8') as f:
            profiles = json.load(f)
            user_profile = next(
                (p for p in profiles['profiles'] if p['id'] == session['user_id']),
                None
            )

        if not user_profile:
            return redirect(url_for('enquiry'))

        # Pass the appointment object directly to template
        return render_template('appointment_detail.html',
                            appointment=appointment,
                            clinic_details=clinic_details,
                            user=user_profile['personal_info'])

    except Exception as e:
        print(f"Error in appointment_detail: {e}")
        return redirect(url_for('enquiry'))

@app.route('/api/appointments/<int:appointment_id>/cancel', methods=['POST'])
@login_required
def cancel_appointment(appointment_id):
    try:
        appointment = Appointment.query.get_or_404(appointment_id)
        if appointment.status == 'upcoming':
            appointment.status = 'cancelled'  # Update status instead of deleting
            db.session.commit()
            return jsonify({'success': True})
    except Exception as e:
        print(f"Error cancelling appointment: {e}")
        db.session.rollback()
        return jsonify({'success': False}), 500
    return jsonify({'success': False}), 400

@app.route('/appointments')
@login_required
def view_appointments():
    appointments = Appointment.query.all()
    upcoming = [apt for apt in appointments if apt.status == 'upcoming']
    past = [apt for apt in appointments if apt.status == 'past']
    
    return render_template('appointments.html', 
                         upcoming_appointments=upcoming,
                         past_appointments=past)

@app.route('/login')
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/iamsmart-login')
def iamsmart_login():
    # Instead of setting session directly, redirect to authentication
    return redirect(url_for('authenticate'))

@app.route('/authenticate')
def authenticate():
    return render_template('authentication.html')

@app.route('/complete-auth')
def complete_auth():
    # This is where the authentication completes
    session['user_id'] = 1  # Set proper user_id
    session['logged_in'] = True
    return redirect(url_for('index'))

@app.route('/iamsmart-register')
def iamsmart_register():
    return redirect(url_for('authorization'))

@app.route('/authorization')
def authorization():
    return render_template('authorization.html')

@app.route('/process-auth')
def process_auth():
    try:
        # Use current_app to get the correct root path
        app_root = current_app.root_path
        json_path = os.path.join(app_root, 'data', 'users.json')
        print(f"Looking for users.json at: {json_path}")

        # Check if file exists and read data
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'users' in data and data['users']:
                    user = data['users'][0]
                    # Store user data in session
                    session['registration_data'] = user
                    print(f"Successfully loaded user data: {user}")
                    return render_template('register_form.html', user=user)
                else:
                    print("Invalid JSON structure: 'users' key not found or empty")
        else:
            print(f"users.json not found at: {json_path}")

        # If we get here, either file doesn't exist or data is invalid
        return redirect(url_for('login'))

    except Exception as e:
        print(f"Error processing user data: {type(e).__name__}: {str(e)}")
        return redirect(url_for('login'))

@app.route('/complete-registration', methods=['POST'])
def complete_registration():
    if 'registration_data' in session:
        user_data = session.get('registration_data')
        
        # Set up login session
        session['user_id'] = user_data['idNo']['Identification']
        session['logged_in'] = True
        
        # Clear registration data but keep login session
        session.pop('registration_data', None)
        
        # Show completion page which will redirect to index
        return render_template('complete.html')
    
    return redirect(url_for('login'))

@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/logout', methods=['POST'])
def logout():
    # Clear all session data
    session.clear()
    return redirect(url_for('login'))

@app.route('/appointment_detail/<int:appointment_id>')
@login_required
def view_appointment_detail(appointment_id):
    try:
        # Get appointment data
        appointment = Appointment.query.get_or_404(appointment_id)
        
        # Get user profile data
        profiles_path = os.path.join(current_app.root_path, 'data', 'profiles.json')
        with open(profiles_path, 'r', encoding='utf-8') as f:
            profiles = json.load(f)
            user_profile = next(
                (p for p in profiles['profiles'] if p['id'] == session['user_id']),
                None
            )

        if not user_profile:
            return redirect(url_for('enquiry'))

        return render_template('appointment_detail.html', 
                            appointment=appointment,
                            user=user_profile['personal_info'])
                            
    except Exception as e:
        print(f"Error loading appointment details: {e}")
        return redirect(url_for('enquiry'))

@app.route('/medical-records')
@login_required
def medical_records():
    records = MedicalRecord.query.order_by(MedicalRecord.visit_date.desc()).all()
    return render_template('medical_records.html', records=records)

@app.route('/medical-records/<int:record_id>')
@login_required
def medical_record_detail(record_id):
    record = MedicalRecord.query.get_or_404(record_id)
    return render_template('medical_record_detail.html', record=record)

@app.route('/input-hl7', methods=['GET', 'POST'])
@login_required
def input_hl7():
    def safe_val(segment, idx):
        return str(segment[idx]) if len(segment) > idx else ""

    def segment_name(seg):
        # seg[0] is usually a string, but sometimes a list (if nested)
        if isinstance(seg[0], str):
            return seg[0]
        elif isinstance(seg[0], list) and len(seg[0]) > 0:
            return seg[0][0]
        return None

    def parse_hl7_message(sample_hl7, user_id):
        h = hl7.parse(sample_hl7)
        print("HL7 segments found:", [segment_name(seg) for seg in h])
        if not any(segment_name(seg) == 'PID' for seg in h):
            raise ValueError("No PID segment found in HL7 message.")
        pid = h.segment('PID')
        name_field = safe_val(pid, 5)
        name_parts = name_field.split('^')
        full_name = ''.join(name_parts)
        # ... the rest of your code unchanged ...

        # Use diagnosis date if available, else today
        dg1_first = next(iter(h.segments('DG1')), None)
        if dg1_first:
            visit_date_str = safe_val(dg1_first, 6)
            visit_date = datetime.strptime(visit_date_str, '%Y%m%d') if visit_date_str else datetime.now()
        else:
            visit_date = datetime.now()

        diagnoses = []
        for dg1 in h.segments('DG1'):
            diag_field = safe_val(dg1, 3)
            diag_parts = diag_field.split('^')
            date_str = safe_val(dg1, 6)
            diagnosis_date = datetime.strptime(date_str, '%Y%m%d') if date_str else visit_date
            diagnoses.append({
                'code': diag_parts[0] if len(diag_parts) > 0 else "",
                'description': diag_parts[1] if len(diag_parts) > 1 else "",
                'coding_system': diag_parts[2] if len(diag_parts) > 2 else "",
                'diagnosis_date': diagnosis_date,
                'status': safe_val(dg1, 7)
            })

        medications = []
        for rxe in h.segments('RXE'):
            med_code_field = safe_val(rxe, 1)
            med_parts = med_code_field.split('^')
            med_code = med_parts[3] if len(med_parts) > 3 else ""
            med_name = med_parts[4] if len(med_parts) > 4 else med_code
            dosage = safe_val(rxe, 2)
            unit = safe_val(rxe, 3)
            route = safe_val(rxe, 4)
            frequency = safe_val(rxe, 5)
            duration_num = safe_val(rxe, 6)
            duration_unit = safe_val(rxe, 7)
            form = safe_val(rxe, 10)
            medications.append({
                'name': med_name,
                'code': med_code,
                'dosage': dosage,
                'unit': unit,
                'route': route,
                'frequency': frequency,
                'duration': f"{duration_num} {duration_unit}".strip(),
                'form': form
            })

        doctor = "Dr. " + session.get('user_name', 'Example')
        clinic = "Sample Clinic"

        return {
            'user_id': user_id,
            'full_name': full_name,
            'visit_date': visit_date,
            'doctor': doctor,
            'clinic': clinic,
            'diagnosis': None,
            'notes': None,
            'hl7_message': sample_hl7
        }, diagnoses, medications

    if request.method == 'POST':
        hl7_text = request.form.get('hl7_data', '')
        # Normalize line endings
        hl7_text = hl7_text.replace('\r\n', '\r').replace('\n', '\r')
        print("HL7 text after normalization:")
        print(repr(hl7_text))
        try:
            patient_info, diagnoses, medications = parse_hl7_message(hl7_text, session['user_id'])
            # ... rest unchanged ...
            medical_record = MedicalRecord(
                user_id=patient_info['user_id'],
                full_name=patient_info['full_name'],
                visit_date=patient_info['visit_date'],
                doctor=patient_info['doctor'],
                clinic=patient_info['clinic'],
                diagnosis=patient_info['diagnosis'],
                notes=patient_info['notes'],
                hl7_message=patient_info['hl7_message']
            )
            diagnosis_count = 0
            for diag in diagnoses:
                diagnosis_count += 1
                diagnosis = Diagnosis(
                    code=diag['code'],
                    description=diag['description'],
                    coding_system=diag['coding_system'],
                    diagnosis_date=diag['diagnosis_date'],
                    status=diag['status']
                )
                medical_record.diagnoses.append(diagnosis)
            medication_count = 0
            for med in medications:
                medication_count += 1
                medication = Medication(
                    name=med['name'],
                    code=med['code'],
                    dosage=med['dosage'],
                    unit=med['unit'],
                    route=med['route'],
                    frequency=med['frequency'],
                    duration=med['duration'],
                    form=med['form']
                )
                medical_record.medications.append(medication)
            db.session.add(medical_record)
            db.session.commit()
            flash(f'Successfully inserted medical record (ID: {medical_record.id}) with {diagnosis_count} diagnoses and {medication_count} medications', 'success')
            return redirect(url_for('medical_records'))
        except Exception as e:
            print(f"Error processing HL7 data: {str(e)}")
            flash(f'Error processing HL7 data: {str(e)}', 'error')
            return render_template('input_hl7.html', error=str(e))
    return render_template('input_hl7.html')