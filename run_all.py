

## ⚙ **run_all.py**

import subprocess
import sys
import time

def run_flask():
    return subprocess.Popen([sys.executable, "app.py"])

def run_streamlit():
    return subprocess.Popen([sys.executable, "-m", "streamlit", "run", "web.py"])

if __name__ == "__main__":
    print("🚀 Đang chạy Flask server...")
    flask_process = run_flask()
    time.sleep(2)  # Chờ Flask chạy trước

    print("🌐 Đang chạy Streamlit app...")
    streamlit_process = run_streamlit()

    flask_process.wait()
    streamlit_process.wait()
