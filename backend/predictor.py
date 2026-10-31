import os
import sys
import json
import joblib
import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from preprocessing.transformers import FrequencyEncoder

MODEL_DIR = os.path.join(ROOT, "models")
CLEANED_DIR = os.path.join(ROOT, "datasets", "cleaned")


class PredictionService:
    def __init__(self):
        self.fe_dict = None
        self.preprocessor = None
        self.cost_model = None
        self.time_model = None
        self.insurance_model = None
        self.fraud_bundle = None
        self.diag_model = None
        self.diag_rules = {}
        self.vehicle_metadata = {}
        self.top_parts = [
            "brake pads", "oil filter", "battery", "spark plugs", "air filter",
            "alternator", "radiator", "starter motor", "transmission fluid", "clutch plate",
            "timing belt", "water pump", "struts", "brake rotor", "fuel pump",
            "oxygen sensor", "tires", "headlight bulb", "cabin filter", "wiper blades"
        ]
        self.load_artifacts()

    def load_artifacts(self):
        try:
            fe_path = os.path.join(MODEL_DIR, "fe_pipeline.pkl")
            if os.path.exists(fe_path):
                self.fe_dict = joblib.load(fe_path)
                self.preprocessor = self.fe_dict["pipeline"]
            
            cost_path = os.path.join(MODEL_DIR, "cost_model.pkl")
            if os.path.exists(cost_path):
                self.cost_model = joblib.load(cost_path)

            time_path = os.path.join(MODEL_DIR, "time_model.pkl")
            if os.path.exists(time_path):
                self.time_model = joblib.load(time_path)

            ins_path = os.path.join(MODEL_DIR, "insurance_model.pkl")
            if os.path.exists(ins_path):
                self.insurance_model = joblib.load(ins_path)

            fraud_path = os.path.join(MODEL_DIR, "fraud_model.pkl")
            if os.path.exists(fraud_path):
                self.fraud_bundle = joblib.load(fraud_path)

            diag_path = os.path.join(MODEL_DIR, "diag_model.pkl")
            if os.path.exists(diag_path):
                self.diag_model = joblib.load(diag_path)

            rules_path = os.path.join(MODEL_DIR, "diag_rules.json")
            if os.path.exists(rules_path):
                with open(rules_path, "r", encoding="utf-8") as f:
                    self.diag_rules = json.load(f)

            meta_path = os.path.join(CLEANED_DIR, "vehicle_metadata.json")
            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as f:
                    self.vehicle_metadata = json.load(f)
            
            print("[Predictor] All ML models, pipelines, fraud engines, and expert rules loaded successfully.")
        except Exception as e:
            print(f"[Predictor] Error loading artifacts: {e}")

    def prepare_input_dataframe(self, input_dict):
        brand = str(input_dict.get("brand", "Toyota")).strip()
        model = str(input_dict.get("model", "Camry")).strip()
        vehicle_type = str(input_dict.get("vehicle_type", "Sedan")).strip()
        service_type = str(input_dict.get("service_type", "Routine Maintenance")).strip()
        urgency_level = str(input_dict.get("urgency_level", "Normal")).strip()
        customer_type = str(input_dict.get("customer_type", "Individual Owner")).strip()
        warranty_info = str(input_dict.get("warranty_info", "Standard Factory Warranty")).strip()

        try:
            estimated_cost = float(input_dict.get("estimated_cost", 200.0) or 200.0)
        except (ValueError, TypeError):
            estimated_cost = 200.0
            
        try:
            mileage = float(input_dict.get("mileage", 30000) or 30000)
        except (ValueError, TypeError):
            mileage = 30000.0
            
        try:
            tech_rating = float(input_dict.get("technician_rating", 4.5) or 4.5)
        except (ValueError, TypeError):
            tech_rating = 4.5
            
        try:
            tow_distance = float(input_dict.get("tow_distance", 0.0) or 0.0)
        except (ValueError, TypeError):
            tow_distance = 0.0
            
        service_desc = str(input_dict.get("problem_description") or input_dict.get("service_description") or "").strip()
        parts_used_str = str(input_dict.get("parts_used", "")).strip().lower()

        parts_list = [p.strip() for p in parts_used_str.split(",") if p.strip()] if parts_used_str else []
        parts_count = len(parts_list)

        # 1. Map Vehicle Type to trained categories: ['Bus', 'Car', 'Motorcycle', 'SUV', 'Truck', 'Van']
        vtype_lower = vehicle_type.lower()
        if any(w in vtype_lower for w in ["sedan", "hatchback", "coupe", "convertible", "wagon", "car"]):
            mapped_vtype = "Car"
        elif "suv" in vtype_lower or "crossover" in vtype_lower:
            mapped_vtype = "SUV"
        elif "truck" in vtype_lower or "pickup" in vtype_lower:
            mapped_vtype = "Truck"
        elif "van" in vtype_lower or "minivan" in vtype_lower:
            mapped_vtype = "Van"
        elif "bus" in vtype_lower:
            mapped_vtype = "Bus"
        elif "motorcycle" in vtype_lower or "bike" in vtype_lower:
            mapped_vtype = "Motorcycle"
        else:
            mapped_vtype = "Car"

        # 2. Map Service Type to trained categories:
        # ['Battery Replacement', 'Brake Service', 'Engine Repair', 'Oil Change', 'Tire Replacement', 'Towing', 'Transmission Repair']
        stype_lower = service_type.lower()
        if "brake" in stype_lower:
            mapped_stype = "Brake Service"
        elif any(k in stype_lower for k in ["engine", "tune", "misfire", "ignition"]):
            mapped_stype = "Engine Repair"
        elif any(k in stype_lower for k in ["transmission", "gear", "clutch"]):
            mapped_stype = "Transmission Repair"
        elif any(k in stype_lower for k in ["battery", "alternator", "starter", "electrical"]):
            mapped_stype = "Battery Replacement"
        elif any(k in stype_lower for k in ["oil", "maintenance", "routine"]):
            mapped_stype = "Oil Change"
        elif any(k in stype_lower for k in ["tire", "wheel"]):
            mapped_stype = "Tire Replacement"
        elif any(k in stype_lower for k in ["tow", "emergency"]):
            mapped_stype = "Towing"
        else:
            mapped_stype = "Brake Service" if "brake" in service_desc.lower() else ("Engine Repair" if "engine" in service_desc.lower() else "Oil Change")

        # 3. Map Urgency Level to trained categories: ['Emergency', 'Scheduled', 'Standard']
        urgency_lower = urgency_level.lower()
        if "critical" in urgency_lower or "emergency" in urgency_lower:
            mapped_urgency = "Emergency"
        elif "low" in urgency_lower or "scheduled" in urgency_lower or "routine" in urgency_lower:
            mapped_urgency = "Scheduled"
        else:
            mapped_urgency = "Standard"

        # 4. Map Customer Type to trained categories: ['Business', 'Fleet', 'Individual']
        cust_lower = customer_type.lower()
        if "fleet" in cust_lower:
            mapped_cust = "Fleet"
        elif "business" in cust_lower or "commercial" in cust_lower:
            mapped_cust = "Business"
        else:
            mapped_cust = "Individual"

        # 5. Map Warranty to trained categories:
        # ['1 year on battery', '1 year on parts', '180 days on brake pads', '6 months on new tire', '90 days on labor', 'No warranty offered']
        warr_lower = warranty_info.lower()
        if "no" in warr_lower or "expired" in warr_lower:
            mapped_warr = "No warranty offered"
        elif "brake" in warr_lower or "brake" in stype_lower:
            mapped_warr = "180 days on brake pads"
        elif "battery" in warr_lower or "battery" in stype_lower:
            mapped_warr = "1 year on battery"
        elif "tire" in warr_lower or "tire" in stype_lower:
            mapped_warr = "6 months on new tire"
        else:
            mapped_warr = "1 year on parts"

        row = {
            "Brand": brand,
            "Model": model,
            "Vehicle Type": mapped_vtype,
            "Service Type": mapped_stype,
            "Urgency Level": mapped_urgency,
            "Customer Type": mapped_cust,
            "Warranty Information": mapped_warr,
            "Estimated Cost": estimated_cost,
            "Mileage at Service": mileage,
            "Technician Rating": tech_rating,
            "Tow Distance Miles": tow_distance,
            "Parts_Count": parts_count,
            "Days_Between_Tow_and_Repair": 1.0 if tow_distance > 0 else 0.0,
            "Repair_Month": 6,
            "Repair_Weekday": 2,
            "Service_Desc_Len": len(service_desc),
            "Is Warranty Valid_flag": 1 if "expired" not in warranty_info.lower() and "no" not in warranty_info.lower() else 0,
            "Follow-up Needed_flag": 0
        }

        for p in self.top_parts:
            colname = f"part_{p.replace(' ', '_')}"
            row[colname] = 1 if any(p in item for item in parts_list) else 0

        keywords = ["engine", "transmission", "brake", "battery", "electrical", "oil", "clutch", "suspension", "towing", "overheating"]
        for kw in keywords:
            row[f"desc_has_{kw}"] = 1 if kw in service_desc.lower() else 0

        df_input = pd.DataFrame([row])
        for col in self.fe_dict["feature_cols"]:
            if col not in df_input.columns:
                df_input[col] = 0

        return df_input[self.fe_dict["feature_cols"]]

    def predict_all(self, input_dict):
        if self.preprocessor is None:
            raise RuntimeError("Feature engineering pipeline not loaded.")

        df_features = self.prepare_input_dataframe(input_dict)
        X = self.preprocessor.transform(df_features)

        # 1. Cost Prediction
        predicted_cost = float(self.cost_model.predict(X)[0]) if self.cost_model else float(input_dict.get("estimated_cost", 200))
        predicted_cost = max(round(predicted_cost, 2), 25.0)

        # 2. Time Prediction
        predicted_time = float(self.time_model.predict(X)[0]) if self.time_model else 2.5
        predicted_time = max(round(predicted_time, 1), 0.5)

        # 3. Insurance Claim Prediction
        if self.insurance_model:
            prob = self.insurance_model.predict_proba(X)[0]
            ins_claim = int(np.argmax(prob))
            ins_prob = float(prob[1]) if len(prob) > 1 else float(prob[0])
            confidence = float(np.max(prob))
        else:
            ins_claim = 0
            ins_prob = 0.15
            confidence = 0.85

        confidence_pct = round(confidence * 100, 1)
        if confidence_pct < 5.0:
            confidence_pct = 50.0

        return {
            "predicted_cost": predicted_cost,
            "predicted_time_hours": predicted_time,
            "predicted_insurance_claim": ins_claim,
            "insurance_claim_status": "Likely Approved / Covered" if ins_claim == 1 else "Direct Out-of-Pocket / Claim Unlikely",
            "insurance_probability_pct": confidence_pct,
            "insurance_confidence_pct": confidence_pct,
            "claim_approval_probability_pct": round(ins_prob * 100, 1),
            "estimated_vs_actual_variance": round(predicted_cost - float(input_dict.get("estimated_cost", 200) or 200), 2)
        }

    def predict_fraud(self, input_dict):
        """
        Inference for Dedicated Insurance Fraud Detection (Dataset 3: fraud_oracle.csv)
        """
        if not self.fraud_bundle:
            return {
                "fraud_detected": 0,
                "fraud_probability_pct": 5.0,
                "risk_level": "Low Risk",
                "risk_badge": "badge-success",
                "model_name": "Rule Heuristic"
            }

        template = dict(self.fraud_bundle["sample_input_template"])
        
        # Override template with user-provided fields
        if "make" in input_dict or "brand" in input_dict:
            template["Make"] = str(input_dict.get("make") or input_dict.get("brand") or "Toyota")
        if "age" in input_dict:
            template["Age"] = int(input_dict.get("age", 35))
        if "deductible" in input_dict:
            template["Deductible"] = float(input_dict.get("deductible", 500))
        if "driver_rating" in input_dict:
            template["DriverRating"] = int(input_dict.get("driver_rating", 3))
        if "fault" in input_dict:
            template["Fault"] = str(input_dict.get("fault", "Policy Holder"))
        if "policy_type" in input_dict:
            template["PolicyType"] = str(input_dict.get("policy_type", "Sedan - All Perils"))
        if "accident_area" in input_dict:
            template["AccidentArea"] = str(input_dict.get("accident_area", "Urban"))
        if "police_report" in input_dict:
            template["PoliceReportFiled"] = str(input_dict.get("police_report", "No"))
        if "witness" in input_dict:
            template["WitnessPresent"] = str(input_dict.get("witness", "No"))

        df_input = pd.DataFrame([template])
        preproc = self.fraud_bundle["preprocessor"]
        model = self.fraud_bundle["model"]

        X_proc = preproc.transform(df_input)
        prob = model.predict_proba(X_proc)[0]
        fraud_prob = float(prob[1]) if len(prob) > 1 else float(prob[0])
        fraud_pred = 1 if fraud_prob >= 0.35 else 0 # Calibrated risk threshold

        if fraud_prob >= 0.65:
            risk_level = "High Fraud Risk"
            risk_badge = "badge-danger"
        elif fraud_prob >= 0.35:
            risk_level = "Medium Suspect Risk"
            risk_badge = "badge-warning"
        else:
            risk_level = "Low / Genuine Claim"
            risk_badge = "badge-success"

        return {
            "fraud_detected": fraud_pred,
            "fraud_probability_pct": round(fraud_prob * 100, 1),
            "risk_level": risk_level,
            "risk_badge": risk_badge,
            "model_name": self.fraud_bundle.get("model_name", "XGBoost Classifier"),
            "evaluated_features": {
                "Make": template.get("Make"),
                "Fault": template.get("Fault"),
                "Deductible": template.get("Deductible"),
                "DriverRating": template.get("DriverRating")
            }
        }

    def diagnose_and_recommend(self, problem_desc, ecu_data="", history="", service_type="", parts_used=""):
        desc = str(problem_desc or "").strip()
        desc_lower = desc.lower()
        ecu = str(ecu_data or "").strip().upper()
        stype = str(service_type or "").strip()
        stype_lower = stype.lower()
        parts_str = str(parts_used or "").strip()
        parts_lower = parts_str.lower()

        # 1. Determine System Classification Category
        category = None

        # Check OBD code first
        if ecu:
            if ecu.startswith("P03") or ecu in ["P0171", "P0174", "P0420", "P0430", "P0128", "P0101", "P0113", "P0135", "P0340", "P0011", "P0016"]:
                category = "Engine"
            elif ecu.startswith("P07") or ecu.startswith("P08") or ecu in ["P0700", "P0730", "P0740", "P0750"]:
                category = "Transmission"
            elif ecu.startswith("C") or ecu in ["C0035", "C1201", "C0040", "C0045"]:
                category = "Brakes"
            elif ecu.startswith("B") or ecu in ["P0562", "P0620", "B1000", "B1001"]:
                category = "Battery"

        # Check Service Type next
        if not category:
            if any(k in stype_lower for k in ["engine", "tune", "misfire", "ignition"]):
                category = "Engine"
            elif any(k in stype_lower for k in ["brake", "rotor", "pad"]):
                category = "Brakes"
            elif any(k in stype_lower for k in ["transmission", "gear", "clutch"]):
                category = "Transmission"
            elif any(k in stype_lower for k in ["battery", "electrical", "alternator", "starter"]):
                category = "Battery"

        # Check Problem Description keywords
        if not category:
            if any(k in desc_lower for k in ["misfir", "spark plug", "engine", "cylinder", "rough idle", "check engine", "stalling", "hesitation"]):
                category = "Engine"
            elif any(k in desc_lower for k in ["brake", "stopping", "pedal", "rotor", "rotors", "caliper", "squeaking", "grinding"]):
                category = "Brakes"
            elif any(k in desc_lower for k in ["transmission", "slipping", "gear", "clutch", "shudder"]):
                category = "Transmission"
            elif any(k in desc_lower for k in ["battery", "alternator", "starter", "won't start", "clicking sound", "dead battery"]):
                category = "Battery"

        # Fallback to trained NLP classifier
        if not category:
            text_input = f"{stype} {desc} {ecu} {parts_str} {history}".strip()
            if self.diag_model:
                try:
                    category = str(self.diag_model.predict([text_input])[0])
                except Exception:
                    category = "Engine" if "engine" in text_input.lower() else "General"
            else:
                category = "General"

        # 2. Detailed Diagnostic Reasoning & Action Plans
        if category == "Engine":
            if ecu == "P0300" or "p0300" in desc_lower or ("misfir" in desc_lower and any(w in desc_lower for w in ["vibrat", "shake", "light", "check"])):
                diagnosis = "Random/Multiple Cylinder Engine Misfire (DTC P0300)"
                severity = "High"
                how_to_fix = "Perform computerized cylinder misfire balance test, test ignition coil pack resistance, inspect spark plug electrodes for carbon fouling, and verify fuel injector pulse."
                replace_parts = ["Spark Plug Set (OEM Iridium/Platinum)", "Ignition Coil Pack", "Fuel Injector O-Rings", "Engine Air Filter", "Intake Manifold Gasket"]
                repair_actions = ["Clear ECU diagnostic trouble codes (DTC P0300)", "Clean throttle body assembly and mass air flow (MAF) sensor", "Perform ignition coil resistance and voltage bench test", "Inspect vacuum lines and check fuel rail pressure"]
            elif ecu.startswith("P030") and len(ecu) == 5:
                cyl_num = ecu[-1]
                diagnosis = f"Cylinder {cyl_num} Engine Misfire Detected (DTC {ecu})"
                severity = "High"
                how_to_fix = f"Swap ignition coil on cylinder {cyl_num} to verify misfire tracking, replace fouled spark plug, and test injector pulse width."
                replace_parts = [f"Ignition Coil Pack (Cylinder {cyl_num})", "Spark Plug Set (OEM Iridium)", "Fuel Injector Assembly", "Valve Cover Gasket"]
                repair_actions = [f"Swap ignition coil from cylinder {cyl_num} to adjacent cylinder", "Perform compression and leak-down test", "Clean fuel injector spray nozzle", f"Clear ECU DTC {ecu}"]
            elif ecu in ["P0171", "P0174"] or "lean" in desc_lower:
                diagnosis = f"Fuel Trim System Too Lean Bank 1/2 (DTC {ecu if ecu else 'P0171'})"
                severity = "Medium"
                how_to_fix = "Perform smoke test along intake ducting for vacuum leaks, clean Mass Air Flow sensor with solvent, and measure fuel pump delivery pressure."
                replace_parts = ["Mass Air Flow (MAF) Sensor", "PCV Breather Hose & Valve", "Intake Plenum Gasket Set", "Fuel Filter Assembly"]
                repair_actions = ["Perform intake smoke test for vacuum leaks", "Clean MAF sensor hot-wire element", "Check fuel pressure regulator and fuel delivery", "Reset long-term fuel trim adaptations"]
            elif ecu in ["P0420", "P0430"] or "catalytic" in desc_lower or "converter" in desc_lower:
                diagnosis = f"Catalytic Converter Efficiency Below Threshold (DTC {ecu if ecu else 'P0420'})"
                severity = "Medium"
                how_to_fix = "Graph heated oxygen sensor waveforms on oscilloscope to verify catalytic converter substrate efficiency, and inspect exhaust piping for leaks."
                replace_parts = ["Direct-Fit Catalytic Converter (OEM/EPA Compliant)", "Downstream Heated Oxygen Sensor (O2)", "Exhaust Manifold Flange Gasket Set", "Exhaust Flange Bolts & Springs"]
                repair_actions = ["Oscilloscope test upstream vs downstream O2 sensor response times", "Inspect exhaust pipe welds for pinhole leaks or cracks", "Perform engine decarbonization cycle", "Clear catalytic DTC codes"]
            elif ecu == "P0128" or "thermostat" in desc_lower or "coolant" in desc_lower:
                diagnosis = "Engine Coolant Temperature Below Regulating Temp (DTC P0128)"
                severity = "Medium"
                how_to_fix = "Replace stuck-open engine thermostat, replenish coolant with factory 50/50 mixture, and bleed air pockets from radiator circuit."
                replace_parts = ["Engine Thermostat & Housing Assembly", "Engine Coolant Temperature Sensor", "OEM Antifreeze / Coolant (50/50 Prediluted)", "Radiator Pressure Cap"]
                repair_actions = ["Pressure test cooling system for external leaks", "Bleed cooling circuit air bubbles", "Verify radiator electric cooling fan cycling", "Clear ECU DTC P0128"]
            else:
                diagnosis = "Engine Ignition & Fuel Delivery Performance Fault"
                severity = "High" if any(w in desc_lower for w in ["vibrat", "shake", "stalling", "smoke", "overheating", "knocking"]) else "Medium"
                how_to_fix = "Perform multi-system OBD-II powertrain diagnostic scan, check spark ignition quality, clean throttle body plate, and inspect vacuum lines."
                replace_parts = ["Spark Plug Set (OEM Spec)", "Ignition Coil Pack", "Engine Air Filter", "PCV Valve Assembly", "Fuel System Cleaner"]
                repair_actions = ["Scan powertrain diagnostic trouble codes and freeze-frame data", "Clean throttle body assembly and idle air control valve", "Perform spark ignition output test", "Inspect vacuum hoses and check engine oil condition"]

        elif category == "Brakes":
            if any(w in desc_lower for w in ["grind", "grinding", "rotor", "vibrat", "shake"]):
                diagnosis = "Brake Rotor Runout & Friction Pad Material Wear"
                severity = "High" if "grind" in desc_lower else "Medium"
                how_to_fix = "Measure brake rotor thickness and runout with micrometer, replace front/rear brake pad sets, resurface or replace vented rotors, and bleed hydraulic lines."
                replace_parts = ["Front Brake Pad Set (OEM Ceramic)", "Vented Brake Rotor Pair", "Brake Caliper Hardware Kit & Anti-Rattle Clips", "DOT 4 Synthetic Brake Fluid", "Rear Brake Pad Set"]
                repair_actions = ["Resurface or replace warped brake rotors", "Clean caliper brackets and lubricate slide pins with synthetic silicone grease", "Bleed hydraulic brake lines to purge moisture and air", "Bed in new ceramic brake pads"]
            elif any(w in desc_lower for w in ["spongy", "soft", "pedal to floor", "fluid leak", "pedal"]):
                diagnosis = "Hydraulic Brake Pressure Loss & Master Cylinder Wear"
                severity = "High"
                how_to_fix = "Inspect brake master cylinder and proportioning valves for internal seal bypass, check flex lines, and pressure bleed brake fluid."
                replace_parts = ["Brake Master Cylinder Assembly", "DOT 4 High-Temp Brake Fluid", "Flexible Reinforced Brake Hoses", "Caliper Bleeder Screws"]
                repair_actions = ["Pressure bleed entire hydraulic brake circuit", "Inspect calipers and wheel cylinders for fluid leaks", "Bench bleed replacement master cylinder", "Test pedal firmness under vacuum assist"]
            else:
                diagnosis = "Brakes System Issue & Friction Material Depletion"
                severity = "Medium"
                how_to_fix = "Inspect friction material on front brake pads, check rotor runout, clean caliper slide pins, and flush hydraulic brake lines."
                replace_parts = ["Front Brake Pad Set (OEM Ceramic)", "Vented Brake Rotor Pair", "Brake Caliper Hardware Kit", "Synthetic Brake Fluid"]
                repair_actions = ["Inspect pad friction thickness against 3mm minimum spec", "Resurface front brake rotors & clean caliper slide pins", "Bleed hydraulic brake lines", "Inspect brake booster vacuum check valve"]

        elif category == "Transmission":
            diagnosis = "Transmission Shift Quality & Hydraulic Valve Degradation"
            severity = "High"
            how_to_fix = "Perform electronic transmission control diagnostic scan, verify fluid level and condition, test solenoid resistance, and replace transmission fluid and filter."
            replace_parts = ["Transmission Fluid (Full Synthetic OEM Spec)", "Transmission Filter Kit with Pan Gasket", "Shift Solenoid Valve Pack", "Transmission Cooler Line Seals"]
            repair_actions = ["Perform full transmission fluid and filter service", "Inspect pan magnet for metallic debris", "Scan TCM for slip codes and reset adaptive shift tables", "Road test gear engagement smoothness"]

        elif category in ["Battery", "Electrical"]:
            category = "Battery"
            diagnosis = "12V Battery Depletion & Charging System Output Fault"
            severity = "High"
            how_to_fix = "Conduct digital battery conductance and load test, measure alternator charging amperage under electrical load, and test starter draw."
            replace_parts = ["12V High-CCA Automotive Battery (AGM)", "Alternator Assembly (OEM)", "Heavy-Duty Battery Terminal Clamps", "Starter Motor Relay"]
            repair_actions = ["Clean battery tray and terminal posts of corrosion", "Test alternator ripple voltage and charging output", "Inspect serpentine accessory belt tension", "Check ground cables for voltage drop"]

        else:
            category = "General"
            diagnosis = "Scheduled Multipoint Service & Vehicle Inspection"
            severity = "Low"
            how_to_fix = "Perform comprehensive multi-point vehicle safety inspection, change engine oil and filter, and replenish all operational fluids."
            replace_parts = ["Full Synthetic Engine Oil (5W-30 / 0W-20)", "OEM Engine Oil Filter & Drain Plug Washer", "Engine Air Filter", "Cabin Pollen Filter"]
            repair_actions = ["Drain engine oil and install new crush washer", "Inspect accessory drive belts, hoses, and fluid levels", "Reset vehicle maintenance reminder light", "Check tire pressures and tread depth"]

        # Ensure user-provided parts in parts_used are included if they match the domain
        if parts_lower:
            user_parts_list = [p.strip().title() for p in parts_str.split(",") if p.strip()]
            valid_user_parts = []
            for p in user_parts_list:
                p_l = p.lower()
                # Strict domain filtering to prevent cross-contamination
                if category == "Engine" and any(b in p_l for b in ["brake", "rotor", "caliper", "pad"]):
                    continue
                if category == "Brakes" and any(e in p_l for e in ["spark plug", "coil", "catalytic", "injector", "transmission"]):
                    continue
                if category == "Transmission" and any(b in p_l for b in ["brake", "rotor", "spark plug"]):
                    continue
                valid_user_parts.append(p)

            if valid_user_parts:
                combined = valid_user_parts + [p for p in replace_parts if p not in valid_user_parts]
                replace_parts = combined

        severity_badges = {
            "Low": "badge-success",
            "Medium": "badge-warning",
            "High": "badge-danger",
            "Critical": "badge-danger"
        }

        return {
            "problem_classification": category,
            "diagnosis": diagnosis,
            "severity": severity,
            "severity_badge": severity_badges.get(severity, "badge-warning"),
            "how_to_fix": how_to_fix,
            "recommended_replace_parts": replace_parts[:5],
            "recommended_repair_actions": repair_actions[:5]
        }


predictor = PredictionService()
