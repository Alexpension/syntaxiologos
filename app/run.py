#!/usr/bin/env python3
"""
Κύριο αρχείο εκτέλεσης για το Project Alex Pension
"""

import sys
import os

# Προσθήκη του current directory στο path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        from app import db
        db.create_all()
        print("✅ Βάση δεδομένων initialized!")

    print("🚀 Starting Alex Pension App...")
    app.run(host='0.0.0.0', port=5001, debug=True)  # ← Αλλαγή σε port 5001