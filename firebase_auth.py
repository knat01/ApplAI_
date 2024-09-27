# firebase_auth.py

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore, auth
import os

# Initialize Firebase app
def initialize_firebase():
    if not firebase_admin._apps:
        # Replace 'path/to/serviceAccountKey.json' with your Firebase service account key path
        cred = credentials.Certificate('path/to/serviceAccountKey.json')
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    return db

# Save user data to Firestore
def save_user_data(user_id, data):
    db = initialize_firebase()
    db.collection('users').document(user_id).set(data)

# Get user data from Firestore
def get_user_data(user_id):
    db = initialize_firebase()
    doc = db.collection('users').document(user_id).get()
    if doc.exists:
        return doc.to_dict()
    else:
        return None

# Save resume to Firebase Storage (optional)
def save_resume_to_storage(user_id, resume_file):
    # Implement saving resume to Firebase Storage if needed
    pass

# Get resume from Firebase Storage (optional)
def get_resume_from_storage(user_id):
    # Implement retrieving resume from Firebase Storage if needed
    pass
