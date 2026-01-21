import os
import sys

# --- THE "DEPLOYMENT HACK" ---
# This block only runs if 'pysqlite3' is installed (i.e., on the Cloud).
# On Windows, it triggers an ImportError and is safely skipped.
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
    print("✅ Successfully swapped SQLite for deployment.")
except ImportError:
    print("⚠️ pysqlite3 not found. Assuming local Windows environment. Creating standard flow...")
    pass
# -----------------------------