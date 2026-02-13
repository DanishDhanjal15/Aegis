import firebase_admin
from firebase_admin import credentials, auth
import os

# Initialize Firebase Admin SDK
def initialize_firebase():
    """Initialize Firebase Admin SDK with service account credentials."""
    try:
        # Check if already initialized
        firebase_admin.get_app()
        print("✅ Firebase Admin already initialized")
    except ValueError:
        # Not initialized yet, so initialize it
        service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH', 'serviceAccountKey.json')
        
        if not os.path.exists(service_account_path):
            print(f"⚠️  Warning: Firebase service account key not found at {service_account_path}")
            print("   Firebase authentication will not work until you add the service account key.")
            print("   See firebase_setup_guide.md for instructions.")
            return False
        
        try:
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase Admin SDK initialized successfully")
            return True
        except Exception as e:
            print(f"❌ Error initializing Firebase Admin SDK: {e}")
            return False

def verify_firebase_token(id_token: str):
    """
    Verify a Firebase ID token and return the decoded token.
    
    Args:
        id_token: The Firebase ID token to verify
        
    Returns:
        dict: Decoded token containing user information (uid, email, etc.)
        
    Raises:
        Exception: If token is invalid or verification fails
    """
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        raise Exception(f"Invalid authentication token: {str(e)}")

def get_user_by_uid(uid: str):
    """
    Get user information by UID.
    
    Args:
        uid: Firebase user UID
        
    Returns:
        UserRecord: Firebase user record
    """
    try:
        user = auth.get_user(uid)
        return user
    except Exception as e:
        raise Exception(f"User not found: {str(e)}")
