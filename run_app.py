import subprocess
import webbrowser
import os

# Path to the Streamlit app
app_path = os.path.join(os.path.dirname(__file__), "main_app.py")

# Start the Streamlit server
subprocess.Popen(["streamlit", "run", app_path])

# Open the app in the default web browser
webbrowser.open("http://localhost:8501")