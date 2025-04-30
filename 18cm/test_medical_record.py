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

def test_parse_hl7():
    h = hl7.parse(sample_hl7)
    
    # Patient info
    pid = h.segment('PID')
    name_field = safe_val(pid, 5)
    name_parts = name_field.split('^')
    patient_info = {
        'id': safe_val(pid, 3),
        'name': {
            'family': name_parts[0] if len(name_parts) > 0 else "",
            'given': name_parts[1] if len(name_parts) > 1 else "",
            'middle': name_parts[2] if len(name_parts) > 2 else ""
        },
        'dob': safe_val(pid, 7),
        'gender': safe_val(pid, 8)
    }
    
    # Diagnoses
    diagnoses = []
    for dg1 in h.segments('DG1'):
        diag_field = safe_val(dg1, 3)
        diag_parts = diag_field.split('^')
        diagnoses.append({
            'code': diag_parts[0] if len(diag_parts) > 0 else "",
            'description': diag_parts[1] if len(diag_parts) > 1 else "",
            'coding_system': diag_parts[2] if len(diag_parts) > 2 else "",
            'date': safe_val(dg1, 6),
            'status': safe_val(dg1, 7)
        })

    # Medications
    medications = []
    for rxe in h.segments('RXE'):
        # rxe[1] is '^^^code^name'
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
    
    # Print parsed data
    print("\nPatient Info:")
    print(f"  ID: {patient_info['id']}")
    print(f"  Name: {patient_info['name']['family']} {patient_info['name']['given']} {patient_info['name']['middle']}")
    print(f"  DOB: {patient_info['dob']}")
    print(f"  Gender: {patient_info['gender']}")
    
    print("\nDiagnoses:")
    for d in diagnoses:
        print(f"  Code: {d['code']}, Desc: {d['description']}, System: {d['coding_system']}, Date: {d['date']}, Status: {d['status']}")
    print("\nMedications:")
    for m in medications:
        print(f"  Name: {m['name']}, Code: {m['code']}, Dosage: {m['dosage']} {m['unit']}, Route: {m['route']}, Freq: {m['frequency']}, Duration: {m['duration']}, Form: {m['form']}")

if __name__ == "__main__":
    test_parse_hl7()