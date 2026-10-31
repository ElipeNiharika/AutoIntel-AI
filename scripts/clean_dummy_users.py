import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.db import get_db_session, User, Vehicle, Prediction, InsurancePrediction, DiagnosisResult, PartsRecommendation

db = get_db_session()
try:
    # Remove dummy test users except admin@autointel.ai
    dummy_users = db.query(User).filter(User.email != "admin@autointel.ai").all()
    for u in dummy_users:
        # Delete related records
        db.query(PartsRecommendation).filter(PartsRecommendation.prediction_id.in_(
            db.query(Prediction.id).filter_by(user_id=u.id)
        )).delete(synchronize_session=False)
        db.query(DiagnosisResult).filter_by(user_id=u.id).delete(synchronize_session=False)
        db.query(InsurancePrediction).filter_by(user_id=u.id).delete(synchronize_session=False)
        db.query(Prediction).filter_by(user_id=u.id).delete(synchronize_session=False)
        db.query(Vehicle).filter_by(user_id=u.id).delete(synchronize_session=False)
        db.delete(u)
    db.commit()
    print(f"Purged {len(dummy_users)} dummy/test users. Only admin@autointel.ai remains.")
except Exception as e:
    db.rollback()
    print("Error purging dummy data:", e)
finally:
    db.close()
