from app import app, db
from app.models import MedicalRecord

def verify_data():
    with app.app_context():
        records = MedicalRecord.query.all()
        
        for record in records:
            print("\nMedical Record:")
            print(f"ID: {record.id}")
            print(f"Patient: {record.full_name}")
            print(f"Visit Date: {record.visit_date}")
            
            print("\nDiagnoses:")
            for diagnosis in record.diagnoses:
                print(f"- {diagnosis.description} ({diagnosis.code})")
                print(f"  Status: {diagnosis.status}")
                
            print("\nMedications:")
            for medication in record.medications:
                print(f"- {medication.name}")
                print(f"  Dosage: {medication.dosage} {medication.unit}")
                print(f"  Frequency: {medication.frequency}")

if __name__ == "__main__":
    verify_data()