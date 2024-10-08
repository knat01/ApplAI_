# firebase_auth.py

import firebase_admin
from firebase_admin import credentials, auth, firestore
import os
import json


# Initialize Firebase app
def initialize_firebase():
    if not firebase_admin._apps:
        cred_dict = {
            "type": "service_account",
            "project_id": os.environ.get("FIREBASE_PROJECT_ID"),
            "private_key_id": os.environ.get("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.environ.get("FIREBASE_PRIVATE_KEY"),
            "client_email": os.environ.get("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.environ.get("FIREBASE_CLIENT_ID"),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url":
            "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": os.environ.get("FIREBASE_CLIENT_CERT_URL")
        }

        # Remove None values and empty strings
        cred_dict = {
            k: v
            for k, v in cred_dict.items() if v is not None and v != ""
        }

        if "private_key" in cred_dict:
            cred_dict["private_key"] = cred_dict["private_key"].replace(
                "\\n", "\n")

        try:
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            print("Firebase initialized successfully.")
        except ValueError as e:
            # App already exists
            print(f"Firebase app already initialized: {e}")
        except Exception as e:
            print(f"Error initializing Firebase: {e}")

    db = firestore.client()
    return db


# Initialize Firestore client
db = initialize_firebase()


def create_user(email, password):
    try:
        user = auth.create_user(email=email, password=password)
        print(f"User created successfully: {user.uid}")
        return user
    except Exception as e:
        #print(f"Error creating user: {e}")
        return None


def login_user(email, password):
    try:
        # NOTE: The Admin SDK does not handle password verification.
        # Implement proper authentication using Firebase Authentication REST API or client SDKs.
        # For demonstration, we're fetching the user by email only.
        user = auth.get_user_by_email(email)
        print(f"User fetched successfully: {user.uid}")
        return user
    except Exception as e:
        #print(f"Error logging in user: {e}")
        return None


def save_user_data(user_id, data):
    if db is None:
        print("Firebase not initialized. Cannot save user data.")
        return
    try:
        db.collection('users').document(user_id).set(data, merge=True)
        #print(f"User data saved for user_id: {user_id}. Data: {data}")
    except Exception as e:
        print(f"Error saving user data: {e}")


def get_user_data(user_id):
    if db is None:
        print("Firebase not initialized. Cannot get user data.")
        return None
    try:
        doc = db.collection('users').document(user_id).get()
        if doc.exists:
            data = doc.to_dict()
            #print(f"User data retrieved for user_id: {user_id}. Data: {data}")
            return data
        else:
            #print(f"No user data found for user_id: {user_id}.")
            return None
    except Exception as e:
        #print(f"Error getting user data: {e}")
        return None
