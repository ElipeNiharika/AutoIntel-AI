import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.db import get_db_session, User, Vehicle, ServiceRequest, Prediction, InsurancePrediction, DiagnosisResult, PartsRecommendation

db = get_db_session()
try:
    # 1. Clean all predictions & recommendations
    db.query(PartsRecommendation).delete(synchronize_session=False)
    db.query(DiagnosisResult).delete(synchronize_session=False)
    db.query(InsurancePrediction).delete(synchronize_session=False)
    db.query(Prediction).delete(synchronize_session=False)
    db.query(ServiceRequest).delete(synchronize_session=False)
    db.query(Vehicle).delete(synchronize_session=False)
    
    # 2. Clean all non-admin users
    db.query(User).filter(User.email != "admin@autointel.ai").delete(synchronize_session=False)
    db.commit()

    admin = db.query(User).filter_by(email="admin@autointel.ai").first()
    print("Database Reset Complete!")
    print(f"Total Users: {db.query(User).count()} (Admin: {admin.email if admin else 'None'})")
    print(f"Total Vehicles: {db.query(Vehicle).count()}")
    print(f"Total Saved Inferences: {db.query(Prediction).count()}")
except Exception as e:
    db.rollback()
    print("Error resetting database:", e)
finally:
    db.close()
