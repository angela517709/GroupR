from app import app, db
from app.models import Appointment  # Add this to import the Appointment model

def init_db():
    with app.app_context():
        # Drop all tables first to ensure clean state
        db.drop_all()
        # Create all tables
        db.create_all()
        print("Database initialized successfully!")

if __name__ == '__main__':
    init_db()