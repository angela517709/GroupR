from app import app, db
from app.models import MedicalRecord, Diagnosis, Medication
from datetime import datetime
import hl7

sample_hl7 = '\r'.join([
    'MSH|^~\\&|ClinicApp|MainClinic|EMR|MainClinic|202504291200||ADT^A01|MSG00002|P|2.3',
    'PID|1||200001^^^ClinicApp||San^Chi^Nan||19651220|M|||88 Health Rd^^City^ST^12345||555-5678',
    'DG1|1||010001^Chronic gastritis without bleed (慢性胃炎未伴有出血)^Combined|||20250429|A',
    'DG1|2||020002^Hypertension (高血壓)^ICD10|||20250429|A',
    'RXE|^^^1005271^Solaray, Betaine HCL with Pepsin, 250 mg|250|MG|PO|BID|14|DAYS||20250429|capsule',
    'RXE|^^^1005270^Marzulene combination tablets 1.0 ES|1.0|ES|PO|BID|14|DAYS||20250429|tablet',
    'RXE|^^^9071105^三仁湯 (Three Kernels Decoction)|||Oral|BID|14|DAYS||20250429|decoction'
])

def safe_val(segment, idx):
    return str(segment[idx]) if len(segment) > idx else ""

def parse_hl7_message(sample_hl7):
    h = hl7.parse(sample_hl7)
    # --- Patient info ---
    pid = h.segment('PID')
    name_field = safe_val(pid, 5)
    name_parts = name_field.split('^')
    full_name = ''.join(name_parts)  # "SanChiNan"
    user_id = 1  # Example static user_id; replace as needed
    dob = safe_val(pid, 7)
    gender = safe_val(pid, 8)
    visit_date = datetime.strptime('20250429', '%Y%m%d')  # Use the first diagnosis date as visit_date

    # --- Diagnoses ---
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

    # --- Medications ---
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

    # --- Extra fields ---
    doctor = "Dr. Example"   # You can parse doctor from HL7 if present, or set to None
    clinic = "Main Clinic"   # You can parse clinic from HL7 if present, or set to None

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

def insert_data():
    # Parse HL7
    patient_info, diagnoses, medications = parse_hl7_message(sample_hl7)

    # Create tables (if not already created)
    db.create_all()

    # Create MedicalRecord
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

    # Add Diagnoses
    for diag in diagnoses:
        diagnosis = Diagnosis(
            code=diag['code'],
            description=diag['description'],
            coding_system=diag['coding_system'],
            diagnosis_date=diag['diagnosis_date'],
            status=diag['status']
        )
        medical_record.diagnoses.append(diagnosis)

    # Add Medications
    for med in medications:
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

    # Insert to DB
    db.session.add(medical_record)
    db.session.commit()
    print(f"Inserted MedicalRecord with id: {medical_record.id}")

if __name__ == '__main__':
    with app.app_context():
        insert_data()
        print("Done.")