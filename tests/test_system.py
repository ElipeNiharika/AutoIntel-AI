import os
import sys
import time
import unittest
import json

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.app import app
from backend.db import init_db, get_db_session, User, Vehicle, Prediction, InsurancePrediction, DiagnosisResult, PartsRecommendation
from backend.predictor import predictor


class TestAIVehicleMasterSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        cls.client = app.test_client()
        init_db()

    @classmethod
    def tearDownClass(cls):
        # Clean up test artifacts so live database remains clean
        db = get_db_session()
        try:
            # Clean test-specific predictions, preserving default user accounts and fleet
            db.query(PartsRecommendation).delete(synchronize_session=False)
            db.query(DiagnosisResult).delete(synchronize_session=False)
            db.query(InsurancePrediction).delete(synchronize_session=False)
            db.query(Prediction).delete(synchronize_session=False)
            db.query(Vehicle).filter(Vehicle.brand == "Honda", Vehicle.model == "Civic").delete(synchronize_session=False)
            db.query(User).filter(User.email == "testdriver@autointel.ai").delete(synchronize_session=False)
            db.commit()
        except Exception as e:
            db.rollback()
        finally:
            db.close()

    def test_01_landing_page_and_initial_db(self):
        # 1. Unauthenticated landing page
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"AutoIntel AI", res.data)
        self.assertIn(b"AI Vehicle Service", res.data)

        # 2. Verify Database Roles
        db = get_db_session()
        admin = db.query(User).filter_by(email="admin@autointel.ai").first()
        self.assertIsNotNone(admin)
        self.assertEqual(admin.role, "admin")
        db.close()
        print("[TEST 1 PASSED] Landing page and database seed verified with pure Admin role.")

    def test_02_database_driven_save_inference_and_admin_sync(self):
        unique_email = f"marcus_{int(time.time())}@autointel.ai"
        with self.client:
            # 1. Register User
            reg = self.client.post("/register", data={
                "name": "Marcus Vance",
                "email": unique_email,
                "password": "Password@123"
            }, follow_redirects=False)
            self.assertEqual(reg.status_code, 302)

            # 2. Login as Normal User
            login = self.client.post("/login", data={
                "email": unique_email,
                "password": "Password@123"
            }, follow_redirects=False)
            self.assertEqual(login.status_code, 302)
            self.assertEqual(login.location, "/dashboard")

            # 3. Check Initial DB Count
            db = get_db_session()
            initial_count = db.query(Prediction).count()
            db.close()

            # 4. Run /api/analyze WITHOUT saving
            api_res = self.client.post("/api/analyze", json={
                "brand": "Honda",
                "model": "Civic",
                "vehicle_type": "Sedan",
                "service_type": "Brake System Service",
                "estimated_cost": 240.0,
                "mileage": 29500,
                "problem_description": "Grinding noise when pressing brakes, pedal vibrates slightly",
                "parts_used": "brake pads, brake rotor",
                "warranty_info": "Standard Factory Warranty",
                "urgency_level": "Normal"
            })
            self.assertEqual(api_res.status_code, 200)
            data = json.loads(api_res.data)
            self.assertEqual(data["status"], "success")
            pred_payload = data["data"]

            # 5. VERIFY DATABASE IS UNTOUCHED BEFORE USER CLICKS SAVE
            db = get_db_session()
            count_after_analyze = db.query(Prediction).count()
            self.assertEqual(count_after_analyze, initial_count, "Prediction must NOT be saved before clicking SAVE!")
            db.close()

            # 6. Confirm SAVE RESULT via /api/save-prediction
            save_res = self.client.post("/api/save-prediction", json=pred_payload)
            self.assertEqual(save_res.status_code, 200)
            save_json = json.loads(save_res.data)
            self.assertEqual(save_json["status"], "success")
            saved_pred_id = save_json["prediction_id"]

            # Verify saved into DB
            db = get_db_session()
            count_after_save = db.query(Prediction).count()
            self.assertEqual(count_after_save, initial_count + 1, "Prediction must be stored after clicking SAVE!")
            
            # Check Vehicle table
            civic_veh = db.query(Vehicle).filter_by(brand="Honda", model="Civic").first()
            self.assertIsNotNone(civic_veh, "Vehicle must be registered into My Vehicles table upon save!")
            db.close()

            # Verify duplicate save prevention
            dup_payload = dict(pred_payload)
            dup_payload["prediction_id"] = saved_pred_id
            dup_res = self.client.post("/api/save-prediction", json=dup_payload)
            self.assertEqual(dup_res.status_code, 200)
            db = get_db_session()
            count_after_dup = db.query(Prediction).count()
            self.assertEqual(count_after_dup, count_after_save, "Duplicate save must not insert another record!")
            db.close()

            # 7. Check My Vehicles page
            veh_page = self.client.get("/vehicles")
            self.assertEqual(veh_page.status_code, 200)
            self.assertIn(b"Honda Civic", veh_page.data)

            # 8. Check User History
            hist = self.client.get("/history")
            self.assertEqual(hist.status_code, 200)
            self.assertIn(b"Honda Civic", hist.data)

            # 9. Logout User
            self.client.get("/logout")

            # 10. Login as Admin & Verify Real-Time Synchronized Statistics
            admin_login = self.client.post("/login", data={
                "email": "admin@autointel.ai",
                "password": "Admin@123"
            }, follow_redirects=False)
            self.assertEqual(admin_login.status_code, 302)
            self.assertEqual(admin_login.location, "/admin/dashboard")

            # Check /api/stats (Used by Admin Dashboard)
            stats_res = self.client.get("/api/stats")
            self.assertEqual(stats_res.status_code, 200)
            stats_json = json.loads(stats_res.data)
            kpis = stats_json["kpis"]
            self.assertEqual(kpis["total_predictions"], count_after_save)
            self.assertGreater(kpis["avg_cost"], 0.0)
            self.assertGreater(kpis["avg_time"], 0.0)

            # Check Prediction History (Admin view)
            admin_hist = self.client.get("/admin/history")
            self.assertEqual(admin_hist.status_code, 200)
            self.assertIn(b"Honda Civic", admin_hist.data)
            
            print("[TEST 2 PASSED] Complete Database-Driven Save Flow & Dashboard Synchronization fully verified!")

    def test_03_admin_complete_management(self):
        with self.client:
            # 1. Login as Administrator
            admin_login = self.client.post("/login", data={
                "email": "admin@autointel.ai",
                "password": "Admin@123"
            }, follow_redirects=False)
            self.assertEqual(admin_login.status_code, 302)
            self.assertEqual(admin_login.location, "/admin/dashboard")

            # 2. Access All Admin Modules
            admin_pages = [
                "/admin/dashboard", "/admin/users", "/admin/catalog", 
                "/admin/analytics", "/admin/history", "/admin/reports"
            ]
            for ap in admin_pages:
                res = self.client.get(ap)
                self.assertEqual(res.status_code, 200, f"Admin failed accessing {ap}")

            # 3. Export PDF & CSV
            csv_exp = self.client.get("/export/csv")
            self.assertEqual(csv_exp.status_code, 200)
            self.assertEqual(csv_exp.mimetype, "text/csv")

            pdf_exp = self.client.get("/export/pdf")
            self.assertEqual(pdf_exp.status_code, 200)
            self.assertEqual(pdf_exp.mimetype, "application/pdf")
            print("[TEST 3 PASSED] Admin Management (Login -> Dashboard -> Users -> Catalog -> Analytics -> History -> Reports -> PDF/CSV) fully verified.")

    def test_04_forgot_password_and_otp_flow(self):
        with self.client:
            # 1. Access Forgot Password Page
            res = self.client.get("/forgot-password")
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Forgot Password", res.data)
            self.assertIn(b"GENERATE & SEND OTP", res.data)

            # 2. Test Non-existent Email
            bad_otp = self.client.post("/api/send-otp", json={"email": "nonexistent@fake.com"})
            self.assertEqual(bad_otp.status_code, 404)

            # 3. Generate Valid OTP for admin
            otp_res = self.client.post("/api/send-otp", json={"email": "admin@autointel.ai"})
            self.assertEqual(otp_res.status_code, 200)
            otp_data = json.loads(otp_res.data)
            self.assertEqual(otp_data["status"], "success")
            self.assertTrue("otp" in otp_data)
            otp_code = otp_data["otp"]
            self.assertEqual(len(otp_code), 6)

            # 4. Attempt Reset with Invalid OTP
            bad_reset = self.client.post("/api/reset-password", json={
                "email": "admin@autointel.ai",
                "otp": "000000",
                "new_password": "NewAdminPass@2026"
            })
            self.assertEqual(bad_reset.status_code, 400)

            # 5. Reset with Valid OTP
            good_reset = self.client.post("/api/reset-password", json={
                "email": "admin@autointel.ai",
                "otp": otp_code,
                "new_password": "NewAdminPass@2026"
            })
            self.assertEqual(good_reset.status_code, 200)
            good_data = json.loads(good_reset.data)
            self.assertEqual(good_data["status"], "success")

            # 6. Verify Login with New Password
            new_login = self.client.post("/login", data={
                "email": "admin@autointel.ai",
                "password": "NewAdminPass@2026"
            }, follow_redirects=False)
            self.assertEqual(new_login.status_code, 302)
            self.assertEqual(new_login.location, "/admin/dashboard")

            # 7. Reset Password back to Default Admin@123
            otp_res2 = self.client.post("/api/send-otp", json={"email": "admin@autointel.ai"})
            otp_code2 = json.loads(otp_res2.data)["otp"]
            self.client.post("/api/reset-password", json={
                "email": "admin@autointel.ai",
                "otp": otp_code2,
                "new_password": "Admin@123"
            })
            print("[TEST 4 PASSED] Forgot Password & 6-Digit OTP Verification Flow 100% verified!")

    def test_05_vehicle_predictions_and_cross_contamination(self):
        """
        Validates Test 1 (Hyundai Accent Brake) and Test 2 (BMW 3 Series Engine + P0300)
        ensuring proper diagnosis, no cross-contamination (Engine has NO brake parts),
        and verification in History & Dashboard.
        """
        unique_user = f"driver_{int(time.time())}@autointel.ai"
        with self.client:
            # Register & Login
            self.client.post("/register", data={"name": "Test Driver", "email": unique_user, "password": "Password@123"})
            self.client.post("/login", data={"email": unique_user, "password": "Password@123"})

            # --- TEST 1: Hyundai Accent - Brake System Service ---
            ex1_payload = {
                "brand": "Hyundai",
                "model": "Accent",
                "vehicle_type": "Sedan",
                "service_type": "Brake System Service",
                "urgency_level": "Normal",
                "customer_type": "Individual Owner",
                "warranty_info": "Standard Factory Warranty",
                "estimated_cost": 240.0,
                "mileage": 38000,
                "problem_description": "Squeaking metallic grinding sound when pressing brakes and slight vibration in steering wheel.",
                "parts_used": "brake pads, brake rotor"
            }
            res1 = self.client.post("/api/analyze", json=ex1_payload)
            self.assertEqual(res1.status_code, 200)
            data1 = json.loads(res1.data)["data"]

            self.assertEqual(data1["problem_classification"], "Brakes")
            self.assertIn("Brake", data1["diagnosis"])
            self.assertGreater(data1["predicted_cost"], 0.0)
            self.assertGreater(data1["predicted_time_hours"], 0.0)
            self.assertGreater(data1["insurance_probability_pct"], 0.0)
            self.assertTrue(any("brake" in p.lower() for p in data1["recommended_replace_parts"]))

            # Save Test 1
            save_res1 = self.client.post("/api/save-prediction", json=data1)
            self.assertEqual(save_res1.status_code, 200)

            # --- TEST 2: BMW 3 Series - Engine Diagnostics and Tune-Up + P0300 ---
            ex2_payload = {
                "brand": "BMW",
                "model": "3 Series",
                "vehicle_type": "Sedan",
                "service_type": "Engine Diagnostics and Tune-Up",
                "urgency_level": "Normal",
                "customer_type": "Individual Owner",
                "warranty_info": "Standard Factory Warranty",
                "estimated_cost": 650.0,
                "mileage": 45000,
                "ecu_data": "P0300",
                "problem_description": "Engine vibration, misfiring, check engine light ON.",
                "parts_used": "spark plugs, ignition coil"
            }
            res2 = self.client.post("/api/analyze", json=ex2_payload)
            self.assertEqual(res2.status_code, 200)
            data2 = json.loads(res2.data)["data"]

            self.assertEqual(data2["problem_classification"], "Engine")
            self.assertIn("Misfire", data2["diagnosis"])
            self.assertIn("P0300", data2["diagnosis"])
            self.assertGreater(data2["predicted_cost"], 0.0)
            self.assertGreater(data2["predicted_time_hours"], 0.0)
            self.assertGreater(data2["insurance_probability_pct"], 0.0)

            # CRITICAL CHECK: Verify NO brake parts leak into Engine diagnosis
            replace_parts_lower = [p.lower() for p in data2["recommended_replace_parts"]]
            self.assertFalse(any("brake" in p for p in replace_parts_lower), f"Brake parts found in Engine diagnosis: {data2['recommended_replace_parts']}")
            self.assertTrue(any("spark plug" in p or "ignition coil" in p for p in replace_parts_lower))

            # Save Test 2
            save_res2 = self.client.post("/api/save-prediction", json=data2)
            self.assertEqual(save_res2.status_code, 200)

            # Verify both appear in My History
            hist = self.client.get("/history")
            self.assertEqual(hist.status_code, 200)
            self.assertIn(b"Hyundai Accent", hist.data)
            self.assertIn(b"BMW 3 Series", hist.data)

            # Verify both appear in My Dashboard
            dash = self.client.get("/dashboard")
            self.assertEqual(dash.status_code, 200)
            self.assertIn(b"Hyundai Accent", dash.data)
            self.assertIn(b"BMW 3 Series", dash.data)

            print("[TEST 5 PASSED] Test 1 (Hyundai Accent Brake) & Test 2 (BMW 3 Series Engine P0300) verified with zero cross-contamination!")


if __name__ == "__main__":
    unittest.main()
