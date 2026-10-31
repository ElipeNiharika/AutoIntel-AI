import os
import sys
import io

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = os.path.abspath(os.path.dirname(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.app import app

if __name__ == "__main__":
    print("=" * 80)
    print(">>> STARTING AI VEHICLE SERVICE, REPAIR & INSURANCE INTELLIGENCE PLATFORM <<<")
    print("=" * 80)
    print("Access the web application at: http://127.0.0.1:5000")
    print("Default Admin: admin@autointel.ai / Admin@123")
    print("Default User:  technician@autointel.ai / Technician@123")
    print("=" * 80)
    app.run(debug=False, host="127.0.0.1", port=5000)
