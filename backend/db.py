import os
import json
from datetime import datetime
from werkzeug.security import generate_password_hash
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, TIMESTAMP, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from sqlalchemy.sql import func

Base = declarative_base()


# 1. Users Table (RBAC)
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="user")
    created_at = Column(TIMESTAMP, server_default=func.now())
    last_login = Column(TIMESTAMP, nullable=True)
    login_count = Column(Integer, default=0)
    is_genuine = Column(Integer, default=1)


# 2. Vehicles Table
class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    brand = Column(String(100), nullable=False)
    model = Column(String(200), nullable=False)
    vehicle_type = Column(String(100), nullable=False)
    fuel_type = Column(String(50), default="Petrol")
    transmission = Column(String(50), default="Automatic")
    manufacturing_year = Column(Integer, default=2020)
    mileage = Column(Integer, default=25000)
    created_at = Column(TIMESTAMP, server_default=func.now())


# 3. Service Requests Table
class ServiceRequest(Base):
    __tablename__ = "service_requests"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    service_type = Column(String(200), nullable=False)
    service_description = Column(Text)
    parts_used = Column(Text)
    estimated_cost = Column(Float, default=0.0)
    total_cost = Column(Float, default=0.0)
    duration_hours = Column(Float, default=0.0)
    technician_rating = Column(Float, default=4.5)
    warranty_info = Column(String(255), default="Standard Factory Warranty")
    insurance_claim_used = Column(Integer, default=0)
    urgency_level = Column(String(50), default="Normal")
    tow_distance = Column(Float, default=0.0)
    status = Column(String(50), default="Completed")
    created_at = Column(TIMESTAMP, server_default=func.now())


Service = ServiceRequest


# 4. Master Unified Predictions Table
class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    service_id = Column(Integer, ForeignKey("service_requests.id"), nullable=True)
    vehicle_info = Column(String(255), nullable=False)
    service_type = Column(String(200), nullable=False)
    predicted_cost = Column(Float, default=0.0)
    predicted_time = Column(Float, default=0.0)
    predicted_insurance_claim = Column(Integer, default=0)
    insurance_probability = Column(Float, default=0.0)
    diagnosis_category = Column(String(100), default="General")
    severity = Column(String(50), default="Normal")
    recommended_action = Column(Text)
    parts_recommendation = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())


# 5. Dedicated Insurance Predictions & Fraud Table
class InsurancePrediction(Base):
    __tablename__ = "insurance_predictions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    policy_type = Column(String(100), default="Sedan - All Perils")
    deductible = Column(Float, default=500.0)
    driver_rating = Column(Integer, default=3)
    claim_covered_pred = Column(Integer, default=0)
    claim_covered_prob = Column(Float, default=0.0)
    fraud_detected_pred = Column(Integer, default=0)
    fraud_risk_prob = Column(Float, default=0.0)
    risk_level = Column(String(50), default="Low")
    created_at = Column(TIMESTAMP, server_default=func.now())


# 6. Dedicated Diagnosis Results Table
class DiagnosisResult(Base):
    __tablename__ = "diagnosis_results"
    id = Column(Integer, primary_key=True, autoincrement=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    symptom_text = Column(Text)
    ecu_code = Column(String(50))
    classified_category = Column(String(100), nullable=False)
    severity = Column(String(50), default="Normal")
    confidence_score = Column(Float, default=0.90)
    root_cause = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())


# 7. Dedicated Parts Recommendations Table
class PartsRecommendation(Base):
    __tablename__ = "parts_recommendations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    diagnosis_id = Column(Integer, ForeignKey("diagnosis_results.id"), nullable=True)
    prediction_id = Column(Integer, ForeignKey("predictions.id"), nullable=True)
    action_type = Column(String(50), default="REPLACE")
    part_name = Column(String(255), nullable=False)
    estimated_part_cost = Column(Float, default=0.0)
    created_at = Column(TIMESTAMP, server_default=func.now())


def get_db_url():
    if os.environ.get("MYSQL_URL"):
        return os.environ.get("MYSQL_URL")
    
    host = os.environ.get("MYSQL_HOST")
    user = os.environ.get("MYSQL_USER")
    password = os.environ.get("MYSQL_PASSWORD")
    db_name = os.environ.get("MYSQL_DB", "ai_vehicle_service")
    port = os.environ.get("MYSQL_PORT", "3306")
    
    if host and user:
        pwd_str = f":{password}" if password else ""
        return f"mysql+pymysql://{user}{pwd_str}@{host}:{port}/{db_name}"
    
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    db_path = os.path.join(root_dir, "database", "ai_vehicle_service.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return f"sqlite:///{db_path}"


_default_url = get_db_url()
try:
    engine = create_engine(_default_url, pool_pre_ping=True)
    with engine.connect() as conn:
        pass
except Exception:
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    db_path = os.path.join(root_dir, "database", "ai_vehicle_service.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    _default_url = f"sqlite:///{db_path}"
    engine = create_engine(_default_url, connect_args={"check_same_thread": False})

SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base.metadata.create_all(bind=engine)


def migrate_user_columns():
    try:
        from sqlalchemy import text
        s = SessionLocal()
        for col_def in [
            "ALTER TABLE users ADD COLUMN last_login TIMESTAMP",
            "ALTER TABLE users ADD COLUMN login_count INTEGER DEFAULT 0",
            "ALTER TABLE users ADD COLUMN is_genuine INTEGER DEFAULT 1"
        ]:
            try:
                s.execute(text(col_def))
                s.commit()
            except Exception:
                s.rollback()
        s.close()
    except Exception:
        pass


def init_db(url=None):
    global engine, SessionLocal
    if url:
        try:
            engine = create_engine(url, pool_pre_ping=True)
            with engine.connect() as conn:
                pass
        except Exception:
            root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            db_path = os.path.join(root_dir, "database", "ai_vehicle_service.db")
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
        SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
        Base.metadata.create_all(bind=engine)
    migrate_user_columns()
    seed_initial_data()


def get_db_session():
    return SessionLocal()


def seed_initial_data():
    migrate_user_columns()
    session = SessionLocal()
    try:
        # 1. Lead Fleet Admin ONLY (is_genuine=0 so not listed in customer accounts)
        admin = session.query(User).filter_by(email="admin@autointel.ai").first()
        if not admin:
            admin = User(
                name="Fleet Administrator",
                email="admin@autointel.ai",
                password_hash=generate_password_hash("Admin@123"),
                role="admin",
                is_genuine=0,
                login_count=1
            )
            session.add(admin)
            session.commit()
    except Exception as e:
        session.rollback()
        print(f"[Seed Warning]: {e}")
    finally:
        session.close()


def save_prediction(user_id, vehicle_info, service_type, cost, time_hrs, ins_claim, ins_prob, diag_cat, severity, action, parts):
    session = SessionLocal()
    try:
        pred = Prediction(
            user_id=user_id,
            vehicle_info=vehicle_info,
            service_type=service_type,
            predicted_cost=cost,
            predicted_time=time_hrs,
            predicted_insurance_claim=ins_claim,
            insurance_probability=ins_prob,
            diagnosis_category=diag_cat,
            severity=severity,
            recommended_action=action,
            parts_recommendation=parts
        )
        session.add(pred)
        session.commit()
        session.refresh(pred)
        
        ins_rec = InsurancePrediction(
            prediction_id=pred.id,
            user_id=user_id,
            claim_covered_pred=ins_claim,
            claim_covered_prob=ins_prob,
            risk_level="Low" if ins_prob > 0.5 else "Standard"
        )
        session.add(ins_rec)
        
        diag_rec = DiagnosisResult(
            prediction_id=pred.id,
            user_id=user_id,
            classified_category=diag_cat,
            severity=severity,
            root_cause=action
        )
        session.add(diag_rec)
        session.commit()
        session.refresh(diag_rec)

        if parts:
            part_list = [p.strip() for p in parts.split(",") if p.strip()]
            for item in part_list:
                part_entry = PartsRecommendation(
                    diagnosis_id=diag_rec.id,
                    prediction_id=pred.id,
                    action_type="REPLACE",
                    part_name=item
                )
                session.add(part_entry)
            session.commit()

        return pred.id
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


seed_initial_data()
