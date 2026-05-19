import sys
import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# When running as a PyInstaller bundle, the extracted files are in the same
# directory as the exe (--onedir). We need that directory on sys.path so that
# `from utils.landmarks import ...` style imports resolve correctly.
if getattr(sys, 'frozen', False):
    bundle_dir = os.path.dirname(sys.executable)
    sys.path.insert(0, bundle_dir)

import uvicorn
from main import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    uvicorn.run(app, host='127.0.0.1', port=port, log_level='error')
