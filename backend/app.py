import os
import sys
import io
import csv
import json
import random
import time
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for, 
    session, jsonify, flash, send_file, Response
)
from werkzeug.security import generate_password_hash, check_password_hash

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.db import (
    init_db, get_db_session, User, Vehicle, ServiceRequest, Prediction, 
    InsurancePrediction, DiagnosisResult, PartsRecommendation, save_prediction
)
from backend.predictor import predictor

app = Flask(
    __name__,
    template_folder=os.path.join(ROOT, "templates"),
    static_folder=os.path.join(ROOT, "static")
)
app.secret_key = os.environ.get("FLASK_SECRET", "ai-vehicle-secret-key-2026-industry-level")

# Initialize database schema and seeds
try:
    init_db()
except Exception as e:
    print(f"[DB Startup Warning]: {e}")


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to access this feature.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in with administrator credentials.", "warning")
            return redirect(url_for("login"))
        if session.get("user_role") != "admin":
            flash("Administrator privileges required.", "danger")
            return redirect(url_for("dashboard_page"))
        return f(*args, **kwargs)
    return decorated_function


# -------------------------------------------------------------
# 1. HOME & AUTHENTICATION (Split Screen Experience)
# -------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("register.html")

        db = get_db_session()
        try:
            existing = db.query(User).filter_by(email=email).first()
            if existing:
                flash("An account with this email already exists.", "danger")
                return render_template("register.html")

            new_user = User(
                name=name,
                email=email,
                password_hash=generate_password_hash(password),
                role="user",
                is_genuine=1,
                login_count=0,
                last_login=None
            )
            db.add(new_user)
            db.commit()
            flash("Account registered successfully! Please sign in.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            db.rollback()
            flash(f"Registration error: {e}", "danger")
        finally:
            db.close()

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        db = get_db_session()
        try:
            user = db.query(User).filter_by(email=email).first()
            if user and check_password_hash(user.password_hash, password):
                session["user_id"] = user.id
                session["user_name"] = user.name
                session["user_email"] = user.email
                session["user_role"] = user.role

                # Dynamically record successful login in database
                user.last_login = datetime.now()
                user.login_count = (user.login_count or 0) + 1
                db.commit()

                flash(f"Welcome back, {user.name}!", "success")
                
                # Check role strictly from MySQL
                if user.role == "admin":
                    return redirect(url_for("admin_dashboard_page"))
                else:
                    return redirect(url_for("dashboard_page"))
            else:
                flash("Invalid email or password.", "danger")
        except Exception as e:
            flash(f"Login error: {e}", "danger")
        finally:
            db.close()

    return render_template("login.html")


@app.route("/forgot-password", methods=["GET"])
def forgot_password():
    return render_template("forgot_password.html")


@app.route("/api/send-otp", methods=["POST"])
def api_send_otp():
    data = request.get_json() or request.form.to_dict()
    email = data.get("email", "").strip().lower()

    if not email:
        return jsonify({"status": "error", "message": "Please enter your registered email address."}), 400

    db = get_db_session()
    try:
        user = db.query(User).filter_by(email=email).first()
        if not user:
            return jsonify({
                "status": "error", 
                "message": "No account found associated with this email address. Please check your spelling or register."
            }), 404

        # Generate 6-digit secure numeric OTP
        otp_code = f"{random.randint(100000, 999999)}"
        session["reset_otp"] = otp_code
        session["reset_email"] = email
        session["reset_otp_time"] = time.time()

        print("=" * 60)
        print(f"[OTP DISPATCH] Generated Password Reset OTP for {email}: {otp_code}")
        print("=" * 60)

        return jsonify({
            "status": "success",
            "message": f"Verification OTP generated successfully! Your 6-Digit OTP code is: {otp_code}",
            "otp": otp_code,
            "email": email
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        db.close()


@app.route("/api/reset-password", methods=["POST"])
def api_reset_password():
    data = request.get_json() or request.form.to_dict()
    email = data.get("email", "").strip().lower()
    entered_otp = data.get("otp", "").strip()
    new_password = data.get("new_password", "").strip()

    if not email or not entered_otp or not new_password:
        return jsonify({"status": "error", "message": "All fields (Email, OTP, New Password) are required."}), 400

    saved_otp = session.get("reset_otp")
    saved_email = session.get("reset_email")
    otp_time = session.get("reset_otp_time", 0)

    # Check OTP expiry (15 minutes)
    if time.time() - otp_time > 900:
        return jsonify({"status": "error", "message": "OTP has expired. Please request a new OTP."}), 400

    # Validate OTP & Email match
    if entered_otp != saved_otp or email != saved_email:
        return jsonify({"status": "error", "message": "Invalid OTP verification code. Please check and re-enter."}), 400

    if len(new_password) < 6:
        return jsonify({"status": "error", "message": "New password must be at least 6 characters long."}), 400

    db = get_db_session()
    try:
        user = db.query(User).filter_by(email=email).first()
        if not user:
            return jsonify({"status": "error", "message": "User account not found."}), 404

        user.password_hash = generate_password_hash(new_password)
        db.commit()

        # Clear session OTP
        session.pop("reset_otp", None)
        session.pop("reset_email", None)
        session.pop("reset_otp_time", None)

        flash("Password updated successfully! Please sign in with your new credentials.", "success")
        return jsonify({
            "status": "success",
            "message": "Password updated successfully in database! Redirecting to login..."
        })
    except Exception as e:
        db.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        db.close()


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("login"))


@app.route("/profile")
@login_required
def profile_page():
    return render_template("profile.html")


# -------------------------------------------------------------
# 2. VEHICLE CHECK & AI ANALYSIS (Source of Truth = SAVE RESULT)
# -------------------------------------------------------------
@app.route("/check", methods=["GET"])
@app.route("/analyze", methods=["GET"])
@app.route("/predict", methods=["GET"])
@login_required
def check_page():
    db = get_db_session()
    try:
        user_vehicles = db.query(Vehicle).filter_by(user_id=session.get("user_id")).all()
        return render_template("analyze.html", metadata=predictor.vehicle_metadata, user_vehicles=user_vehicles)
    finally:
        db.close()


@app.route("/api/analyze", methods=["POST"])
@app.route("/api/predict", methods=["POST"])
@login_required
def api_analyze():
    """
    Runs Real Tabular ML Inference & Diagnostic Agent.
    IMPORTANT: Does NOT save to database until the user explicitly clicks 'SAVE RESULT'.
    """
    data = request.get_json() or request.form.to_dict()
    try:
        # 1. Run Pure Tabular ML Models (Cost, Time, Insurance Claim)
        pred_res = predictor.predict_all(data)
        
        # 2. Run NLP Diagnostic Agent & Rule Matrix
        desc = data.get("problem_description") or data.get("service_description") or ""
        ecu = data.get("ecu_data", "")
        stype = data.get("service_type", "General Service")
        parts_used = data.get("parts_used", "")
        diag_res = predictor.diagnose_and_recommend(
            problem_desc=desc,
            ecu_data=ecu,
            service_type=stype,
            parts_used=parts_used
        )

        # 3. Merge Consolidated Results
        consolidated = {**pred_res, **diag_res}

        user_id = session.get("user_id")
        brand = data.get("brand", "").strip() or "Vehicle"
        model = data.get("model", "").strip()
        vtype = data.get("vehicle_type", "Sedan").strip()
        fuel = data.get("fuel_type", "Petrol").strip()
        trans = data.get("transmission", "Automatic").strip()
        try:
            year = int(data.get("manufacturing_year", 2021))
        except (ValueError, TypeError):
            year = 2021
        try:
            mileage = int(data.get("mileage", 35000))
        except (ValueError, TypeError):
            mileage = 35000

        consolidated["vehicle_info"] = f"{brand} {model} ({vtype})".strip()
        consolidated["service_type"] = stype
        consolidated["brand"] = brand
        consolidated["model"] = model
        consolidated["vehicle_type"] = vtype
        consolidated["fuel_type"] = fuel
        consolidated["transmission"] = trans
        consolidated["manufacturing_year"] = year
        consolidated["mileage"] = mileage
        consolidated["saved"] = False

        return jsonify({"status": "success", "data": consolidated})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/save-prediction", methods=["POST"])
@login_required
def api_save_prediction():
    """
    Explicitly saves or confirms a generated ML prediction in MySQL database.
    Increments Total System Inferences and ensures the vehicle is recorded in the user's fleet.
    """
    data = request.get_json() or request.form.to_dict()
    try:
        user_id = session.get("user_id")

        if data.get("prediction_id"):
            return jsonify({
                "status": "success",
                "prediction_id": data.get("prediction_id"),
                "message": "Prediction is already saved in MySQL database."
            })
        vehicle_info = data.get("vehicle_info", "Vehicle")
        service_type = data.get("service_type", "General Service")
        cost = float(data.get("predicted_cost", 0.0))
        time_hrs = float(data.get("predicted_time_hours") or data.get("predicted_time", 0.0))
        ins_claim = int(data.get("predicted_insurance_claim", 0))
        ins_prob = float(data.get("insurance_probability_pct", 0.0)) / 100.0 if "insurance_probability_pct" in data else float(data.get("insurance_probability", 0.0))
        diag_cat = data.get("problem_classification") or data.get("diagnosis_category", "General")
        severity = data.get("severity", "Normal")
        action = data.get("how_to_fix") or data.get("recommended_action", "Standard inspection")
        
        parts_data = data.get("recommended_replace_parts") or data.get("parts_recommendation", "")
        if isinstance(parts_data, list):
            parts_str = ", ".join(parts_data)
        else:
            parts_str = str(parts_data)

        # Ensure vehicle is registered in the user's fleet (My Vehicles)
        brand = data.get("brand") or (vehicle_info.split()[0] if vehicle_info else "")
        model = data.get("model") or (" ".join(vehicle_info.split()[1:]).split("(")[0].strip() if vehicle_info else "")
        vtype = data.get("vehicle_type", "Sedan")
        fuel = data.get("fuel_type", "Petrol")
        trans = data.get("transmission", "Automatic")
        try:
            year = int(data.get("manufacturing_year", 2021))
        except (ValueError, TypeError):
            year = 2021
        try:
            mileage = int(data.get("mileage", 35000))
        except (ValueError, TypeError):
            mileage = 35000

        if user_id and brand and model and brand != "Vehicle":
            db_veh = get_db_session()
            try:
                existing_veh = db_veh.query(Vehicle).filter_by(
                    user_id=user_id,
                    brand=brand,
                    model=model
                ).first()
                if not existing_veh:
                    new_veh = Vehicle(
                        user_id=user_id,
                        brand=brand,
                        model=model,
                        vehicle_type=vtype,
                        fuel_type=fuel,
                        transmission=trans,
                        manufacturing_year=year,
                        mileage=mileage
                    )
                    db_veh.add(new_veh)
                    db_veh.commit()
                else:
                    if mileage > (existing_veh.mileage or 0):
                        existing_veh.mileage = mileage
                        db_veh.commit()
            except Exception as e_v:
                db_veh.rollback()
                print(f"[Vehicle Auto-Registration Notice]: {e_v}")
            finally:
                db_veh.close()

        pred_id = save_prediction(
            user_id=user_id,
            vehicle_info=vehicle_info,
            service_type=service_type,
            cost=cost,
            time_hrs=time_hrs,
            ins_claim=ins_claim,
            ins_prob=ins_prob,
            diag_cat=diag_cat,
            severity=severity,
            action=action,
            parts=parts_str
        )

        return jsonify({
            "status": "success",
            "prediction_id": pred_id,
            "message": "Prediction and vehicle successfully saved to MySQL database."
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


# -------------------------------------------------------------
# 3. MY VEHICLES FLEET MANAGEMENT (CRUD)
# -------------------------------------------------------------
@app.route("/vehicles", methods=["GET"])
@login_required
def vehicles_page():
    db = get_db_session()
    try:
        # User only sees their own vehicles
        user_vehicles = db.query(Vehicle).filter_by(user_id=session.get("user_id")).all()
        return render_template("vehicles.html", metadata=predictor.vehicle_metadata, user_vehicles=user_vehicles)
    finally:
        db.close()


@app.route("/vehicles/add", methods=["GET", "POST"])
@login_required
def add_vehicle_page():
    if request.method == "POST":
        brand = request.form.get("brand", "").strip()
        model = request.form.get("model", "").strip()
        vehicle_type = request.form.get("vehicle_type", "Sedan").strip()
        fuel_type = request.form.get("fuel_type", "Petrol").strip()
        transmission = request.form.get("transmission", "Automatic").strip()
        manufacturing_year = int(request.form.get("manufacturing_year", 2021))
        mileage = int(request.form.get("mileage", 25000))

        db = get_db_session()
        try:
            veh = Vehicle(
                user_id=session.get("user_id"),
                brand=brand,
                model=model,
                vehicle_type=vehicle_type,
                fuel_type=fuel_type,
                transmission=transmission,
                manufacturing_year=manufacturing_year,
                mileage=mileage
            )
            db.add(veh)
            db.commit()
            flash(f"Vehicle {brand} {model} added to profile!", "success")
            return redirect(url_for("vehicles_page"))
        except Exception as e:
            db.rollback()
            flash(f"Error adding vehicle: {e}", "danger")
        finally:
            db.close()

    return render_template("add_vehicle.html", metadata=predictor.vehicle_metadata)


@app.route("/vehicles/edit/<int:vehicle_id>", methods=["GET", "POST"])
@login_required
def edit_vehicle_page(vehicle_id):
    db = get_db_session()
    try:
        veh = db.query(Vehicle).filter_by(id=vehicle_id, user_id=session.get("user_id")).first()
        if not veh:
            flash("Vehicle not found or unauthorized.", "danger")
            return redirect(url_for("vehicles_page"))

        if request.method == "POST":
            veh.brand = request.form.get("brand", veh.brand).strip()
            veh.model = request.form.get("model", veh.model).strip()
            veh.vehicle_type = request.form.get("vehicle_type", veh.vehicle_type).strip()
            veh.fuel_type = request.form.get("fuel_type", veh.fuel_type).strip()
            veh.transmission = request.form.get("transmission", veh.transmission).strip()
            veh.manufacturing_year = int(request.form.get("manufacturing_year", veh.manufacturing_year))
            veh.mileage = int(request.form.get("mileage", veh.mileage))
            db.commit()
            flash("Vehicle profile updated successfully!", "success")
            return redirect(url_for("vehicles_page"))

        return render_template("edit_vehicle.html", vehicle=veh, metadata=predictor.vehicle_metadata)
    finally:
        db.close()


@app.route("/vehicles/delete/<int:vehicle_id>", methods=["GET", "POST"])
@login_required
def delete_vehicle_action(vehicle_id):
    db = get_db_session()
    try:
        veh = db.query(Vehicle).filter_by(id=vehicle_id, user_id=session.get("user_id")).first()
        if veh:
            db.delete(veh)
            db.commit()
            flash("Vehicle removed from your profile.", "info")
        else:
            flash("Vehicle not found or unauthorized.", "danger")
        return redirect(url_for("vehicles_page"))
    finally:
        db.close()


# -------------------------------------------------------------
# 4. MY SERVICE HISTORY (User-Isolated)
# -------------------------------------------------------------
@app.route("/history", methods=["GET"])
@login_required
def history_page():
    db = get_db_session()
    try:
        query = db.query(Prediction).order_by(Prediction.created_at.desc())
        # Non-admin users strictly see only their own history
        if session.get("user_role") != "admin":
            query = query.filter(Prediction.user_id == session.get("user_id"))

        predictions = query.limit(200).all()
        return render_template("history.html", predictions=predictions)
    finally:
        db.close()


# -------------------------------------------------------------
# 5. USER & ADMIN DASHBOARDS
# -------------------------------------------------------------
@app.route("/dashboard", methods=["GET"])
@login_required
def dashboard_page():
    # If an admin accesses /dashboard, route them to their control center
    if session.get("user_role") == "admin":
        return redirect(url_for("admin_dashboard_page"))
    
    db = get_db_session()
    try:
        user_id = session.get("user_id")
        recent_checks = db.query(Prediction).filter_by(user_id=user_id).order_by(Prediction.created_at.desc()).limit(10).all()
        user_vehicles = db.query(Vehicle).filter_by(user_id=user_id).order_by(Vehicle.created_at.desc()).all()
        return render_template("dashboard.html", recent_checks=recent_checks, user_vehicles=user_vehicles)
    finally:
        db.close()


@app.route("/admin", methods=["GET"])
@app.route("/admin/dashboard", methods=["GET"])
@admin_required
def admin_dashboard_page():
    db = get_db_session()
    try:
        recent_checks = db.query(Prediction).order_by(Prediction.created_at.desc()).limit(10).all()
        return render_template("admin_dashboard.html", recent_checks=recent_checks)
    finally:
        db.close()


@app.route("/admin/users", methods=["GET"])
@admin_required
def admin_users_page():
    db = get_db_session()
    try:
        # Strictly display genuine registered users who have successfully logged in
        users = db.query(User).filter(
            User.is_genuine == 1,
            User.login_count > 0,
            User.last_login.isnot(None),
            ~User.email.like("%@autointel.ai"),
            ~User.name.in_(["Test Driver", "Marcus Vance", "Fleet Technician", "Vehicle Owner"])
        ).order_by(User.created_at.desc()).all()

        users_data = []
        for u in users:
            v_cnt = db.query(Vehicle).filter_by(user_id=u.id).count()
            a_cnt = db.query(Prediction).filter_by(user_id=u.id).count()
            users_data.append({
                "user": u,
                "vehicle_count": v_cnt,
                "analysis_count": a_cnt
            })
        return render_template("admin_users.html", users_data=users_data)
    finally:
        db.close()


@app.route("/admin/catalog", methods=["GET"])
@admin_required
def admin_catalog_page():
    return render_template("admin_catalog.html", metadata=predictor.vehicle_metadata)


@app.route("/admin/analytics", methods=["GET"])
@admin_required
def admin_analytics_page():
    return render_template("admin_analytics.html")


@app.route("/admin/history", methods=["GET"])
@admin_required
def admin_history_page():
    db = get_db_session()
    try:
        # Strictly uses the EXACT SAME predictions table as the Admin Dashboard
        predictions = db.query(Prediction).order_by(Prediction.created_at.desc()).limit(200).all()
        return render_template("admin_history.html", predictions=predictions)
    finally:
        db.close()


@app.route("/admin/reports", methods=["GET"])
@admin_required
def admin_reports_page():
    return render_template("admin_reports.html")


@app.route("/api/stats", methods=["GET"])
@login_required
def api_stats():
    """
    Computes real, dynamic MySQL aggregates strictly from saved Prediction records.
    Source of Truth: predictions table in MySQL.
    """
    db = get_db_session()
    try:
        query = db.query(Prediction)
        if session.get("user_role") != "admin":
            query = query.filter(Prediction.user_id == session.get("user_id"))

        preds = query.all()
        total_count = len(preds)
        
        if total_count > 0:
            valid_costs = [p.predicted_cost for p in preds if p.predicted_cost is not None and p.predicted_cost > 0]
            avg_cost = round(sum(valid_costs) / len(valid_costs), 2) if valid_costs else 0.0

            valid_times = [p.predicted_time for p in preds if p.predicted_time is not None and p.predicted_time > 0]
            avg_time = round(sum(valid_times) / len(valid_times), 1) if valid_times else 0.0

            valid_ins = [p for p in preds if p.predicted_insurance_claim is not None]
            if len(valid_ins) > 0:
                insurance_approvals = sum(1 for p in valid_ins if p.predicted_insurance_claim == 1)
                insurance_pct = round((insurance_approvals / len(valid_ins)) * 100, 1)
            else:
                insurance_pct = 0.0
        else:
            avg_cost = 0.0
            avg_time = 0.0
            insurance_pct = 0.0

        cat_counts = {}
        for p in preds:
            c = p.diagnosis_category or "General"
            cat_counts[c] = cat_counts.get(c, 0) + 1

        svc_counts = {}
        for p in preds:
            s = p.service_type or "General Maintenance"
            svc_counts[s] = svc_counts.get(s, 0) + 1

        parts_counter = {}
        for p in preds:
            if p.parts_recommendation:
                items = [item.strip() for item in p.parts_recommendation.split(",") if item.strip()]
                for it in items:
                    parts_counter[it] = parts_counter.get(it, 0) + 1
        top_parts_sorted = sorted(parts_counter.items(), key=lambda x: x[1], reverse=True)[:6]

        return jsonify({
            "status": "success",
            "kpis": {
                "total_predictions": total_count,
                "avg_cost": avg_cost,
                "avg_time": avg_time,
                "insurance_pct": insurance_pct
            },
            "charts": {
                "categories": {
                    "labels": list(cat_counts.keys()),
                    "values": list(cat_counts.values())
                },
                "services": {
                    "labels": list(svc_counts.keys()),
                    "values": list(svc_counts.values())
                },
                "top_parts": {
                    "labels": [p[0] for p in top_parts_sorted],
                    "values": [p[1] for p in top_parts_sorted]
                }
            }
        })
    finally:
        db.close()


# -------------------------------------------------------------
# 6. EXPORT MODULES (CSV & PDF)
# -------------------------------------------------------------
@app.route("/export/csv", methods=["GET"])
@login_required
def export_csv():
    db = get_db_session()
    try:
        query = db.query(Prediction).order_by(Prediction.created_at.desc())
        if session.get("user_role") != "admin":
            query = query.filter(Prediction.user_id == session.get("user_id"))

        preds = query.all()
        si = io.StringIO()
        cw = csv.writer(si)
        cw.writerow([
            "Check ID", "Date", "Vehicle Info", "Service Type", "Estimated Cost ($)", 
            "Turnaround Time (Hrs)", "Insurance Covered", "Insurance Confidence (%)",
            "Possible Problem", "Severity", "Recommended Service", "Parts Action Plan"
        ])
        for p in preds:
            cw.writerow([
                p.id,
                p.created_at.strftime("%Y-%m-%d %H:%M") if p.created_at else "N/A",
                p.vehicle_info,
                p.service_type,
                f"{p.predicted_cost:.2f}",
                f"{p.predicted_time:.1f}",
                "Yes" if p.predicted_insurance_claim == 1 else "No",
                f"{(p.insurance_probability or 0.0) * 100:.1f}%",
                p.diagnosis_category,
                p.severity,
                p.recommended_action,
                p.parts_recommendation
            ])
        output = Response(si.getvalue(), mimetype="text/csv")
        output.headers["Content-Disposition"] = "attachment; filename=AutoIntel_Service_Report.csv"
        return output
    finally:
        db.close()


@app.route("/export/pdf", methods=["GET"])
@login_required
def export_pdf():
    db = get_db_session()
    try:
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        query = db.query(Prediction).order_by(Prediction.created_at.desc())
        if session.get("user_role") != "admin":
            query = query.filter(Prediction.user_id == session.get("user_id"))

        preds = query.limit(50).all()
        
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=landscape(letter),
            rightMargin=20,
            leftMargin=20,
            topMargin=30,
            bottomMargin=30
        )
        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=18,
            textColor=colors.HexColor("#1e293b"),
            spaceAfter=10
        )
        elements.append(Paragraph("AutoIntel AI - Vehicle Service & Diagnosis Audit Report", title_style))
        elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total Records: {len(preds)}", styles["Normal"]))
        elements.append(Spacer(1, 15))

        table_data = [
            ["ID", "Date", "Vehicle Info", "Service Type", "Cost ($)", "Time (h)", "Insurance", "Diagnosis", "Severity"]
        ]
        for p in preds:
            table_data.append([
                str(p.id),
                p.created_at.strftime("%Y-%m-%d") if p.created_at else "",
                (p.vehicle_info or "")[:20],
                (p.service_type or "")[:18],
                f"${p.predicted_cost:.2f}",
                f"{p.predicted_time:.1f}h",
                "Covered" if p.predicted_insurance_claim == 1 else "Direct",
                (p.diagnosis_category or "")[:12],
                (p.severity or "")
            ])

        t = Table(table_data, colWidths=[30, 65, 120, 110, 60, 50, 65, 80, 65])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(t)
        doc.build(elements)
        buf.seek(0)

        return send_file(
            buf,
            as_attachment=True,
            download_name="AutoIntel_Service_Summary.pdf",
            mimetype="application/pdf"
        )
    finally:
        db.close()


@app.route("/api/vehicle-metadata")
def api_vehicle_metadata():
    return jsonify(predictor.vehicle_metadata)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
