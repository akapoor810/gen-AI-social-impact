from flask import send_file
import os
import json
from flask import Flask, request, jsonify, Response
from llmproxy import *

# JSON file to store user sessions
SESSION_FILE = "session_store.json"

### --- SESSION MANAGEMENT FUNCTIONS --- ###
def load_sessions():
    """Load stored sessions from a JSON file."""
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "r") as file:
            try:
                session_data = json.load(file)
                print(f"Loaded session data: {session_data}")
                return session_data
            except json.JSONDecodeError:
                print("Error loading session data, returning empty dict.")
                return {}  # If file is corrupted, return an empty dict
    print("No session file found. Returning empty dictionary.")
    return {}

def save_sessions(session_dict):
    """Save sessions to a JSON file."""
    print(f"Saving session data: {session_dict}")
    with open(SESSION_FILE, "w") as file:
        json.dump(session_dict, file, indent=4)
    print("Session data saved.")