import firebase_admin
from firebase_admin import credentials, auth, firestore
import os
import json

# Initialize Firebase app
cred_dict = {
    "type": "service_account",
    "project_id": os.environ.get("FIREBASE_PROJECT_ID"),
    "private_key_id": os.environ.get("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.environ.get("FIREBASE_PRIVATE_KEY"),
    "client_email": os.environ.get("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.environ.get("FIREBASE_CLIENT_ID"),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": os.environ.get("FIREBASE_CLIENT_CERT_URL")
}

# Remove None values and empty strings
cred_dict = {k: v for k, v in cred_dict.items() if v is not None and v != ""}

if "private_key" in cred_dict:
    cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")

try:
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    print(f"Error initializing Firebase: {e}")
    db = None

def create_user(email, password):
    try:
        user = auth.create_user(email=email, password=password)
        return user
    except Exception as e:
        print(f"Error creating user: {e}")
        return None

def login_user(email, password):
    try:
        user = auth.get_user_by_email(email)
        # In a real-world scenario, you'd verify the password here
        return user
    except Exception as e:
        print(f"Error logging in user: {e}")
        return None

def save_user_data(user_id, data):
    if db is None:
        print("Firebase not initialized. Cannot save user data.")
        return
    try:
        db.collection('users').document(user_id).set(data, merge=True)
    except Exception as e:
        print(f"Error saving user data: {e}")

def get_user_data(user_id):
    if db is None:
        print("Firebase not initialized. Cannot get user data.")
        return None
    try:
        doc = db.collection('users').document(user_id).get()
        return doc.to_dict() if doc.exists else None
    except Exception as e:
        print(f"Error getting user data: {e}")
        return None
