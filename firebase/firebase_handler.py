"""
Firebase Handler Module - Handles user state, bookmarks, and metrics
"""
import os
import json
import datetime
from dotenv import load_dotenv

# Conditionally import firebase_admin
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

# Load environment variables
load_dotenv()

class FirebaseHandler:
    def __init__(self):
        """Initialize the Firebase handler with optional connection to Firebase"""
        self.db = None
        self.connected = False
        
        if not FIREBASE_AVAILABLE:
            print("Firebase packages not installed. Running in offline mode.")
            return
            
        # Try to initialize Firebase connection
        try:
            firebase_key_path = os.getenv("FIREBASE_KEY_PATH")
            
            if firebase_key_path and os.path.exists(firebase_key_path):
                # Initialize Firebase with credentials
                cred = credentials.Certificate(firebase_key_path)
                firebase_admin.initialize_app(cred)
                
                # Initialize Firestore
                self.db = firestore.client()
                self.connected = True
                print("Connected to Firebase successfully")
            else:
                print("Firebase key not found. Running in offline mode.")
                
        except Exception as e:
            print(f"Error connecting to Firebase: {e}")
    
    def save_user_progress(self, user_id, scene_id):
        """
        Save the user's current scene
        
        Args:
            user_id (str): The user's ID
            scene_id (str): The current scene ID
            
        Returns:
            bool: Success status
        """
        if not self.connected:
            # In offline mode, save to a local file
            return self._save_offline_data("user_progress", user_id, {
                "current_scene": scene_id,
                "updated_at": datetime.datetime.now().isoformat()
            })
            
        try:
            user_ref = self.db.collection('users').document(user_id)
            user_ref.set({
                'current_scene': scene_id,
                'updated_at': firestore.SERVER_TIMESTAMP
            }, merge=True)
            return True
        except Exception as e:
            print(f"Error saving user progress: {e}")
            return False
    
    def get_user_state(self, user_id):
        """
        Get the user's current state
        
        Args:
            user_id (str): The user's ID
            
        Returns:
            dict: User state data
        """
        if not self.connected:
            # In offline mode, get from a local file
            return self._get_offline_data("user_progress", user_id)
            
        try:
            user_ref = self.db.collection('users').document(user_id)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                return user_doc.to_dict()
            else:
                return {"current_scene": "start", "first_time": True}
        except Exception as e:
            print(f"Error getting user state: {e}")
            return {"current_scene": "start", "error": str(e)}
    
    def save_choice(self, user_id, scene_id, choice):
        """
        Save the user's choice for a scene
        
        Args:
            user_id (str): The user's ID
            scene_id (str): The scene ID
            choice (dict): The choice made by the user
            
        Returns:
            bool: Success status
        """
        if not self.connected:
            # In offline mode, save to a local file
            return self._save_offline_data("user_choices", user_id, {
                scene_id: {
                    "choice_id": choice.get("id"),
                    "choice_text": choice.get("text"),
                    "timestamp": datetime.datetime.now().isoformat()
                }
            })
            
        try:
            # Save to choices collection with user and scene info
            choice_data = {
                'user_id': user_id,
                'scene_id': scene_id,
                'choice_id': choice.get("id"),
                'choice_text': choice.get("text"),
                'timestamp': firestore.SERVER_TIMESTAMP
            }
            
            self.db.collection('choices').add(choice_data)
            
            # Also update user document with latest choice
            user_ref = self.db.collection('users').document(user_id)
            user_ref.set({
                'choices': {
                    scene_id: {
                        'choice_id': choice.get("id"),
                        'choice_text': choice.get("text"),
                        'timestamp': firestore.SERVER_TIMESTAMP
                    }
                }
            }, merge=True)
            
            return True
        except Exception as e:
            print(f"Error saving choice: {e}")
            return False
    
    def log_metrics(self, user_id, data):
        """
        Log usage metrics
        
        Args:
            user_id (str): The user's ID
            data (dict): Metrics data
            
        Returns:
            bool: Success status
        """
        if not self.connected:
            # In offline mode, save to a local file
            metrics_data = data.copy()
            metrics_data["timestamp"] = datetime.datetime.now().isoformat()
            return self._save_offline_data("metrics", user_id, metrics_data, append=True)
            
        try:
            # Add timestamp
            metrics_data = data.copy()
            metrics_data['user_id'] = user_id
            metrics_data['timestamp'] = firestore.SERVER_TIMESTAMP
            
            # Save to metrics collection
            self.db.collection('metrics').add(metrics_data)
            return True
        except Exception as e:
            print(f"Error logging metrics: {e}")
            return False
    
    def _save_offline_data(self, data_type, user_id, data, append=False):
        """Save data to a local file when offline"""
        # Create directory structure
        os.makedirs("offline_data", exist_ok=True)
        os.makedirs(f"offline_data/{data_type}", exist_ok=True)
        
        file_path = f"offline_data/{data_type}/{user_id}.json"
        
        if append and os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    existing_data = json.load(f)
                
                if isinstance(existing_data, list):
                    existing_data.append(data)
                    with open(file_path, 'w') as f:
                        json.dump(existing_data, f, indent=2)
                else:
                    with open(file_path, 'w') as f:
                        json.dump([existing_data, data], f, indent=2)
            except Exception as e:
                print(f"Error appending to offline data: {e}")
                return False
        else:
            try:
                with open(file_path, 'w') as f:
                    if append:
                        json.dump([data], f, indent=2)
                    else:
                        json.dump(data, f, indent=2)
            except Exception as e:
                print(f"Error saving offline data: {e}")
                return False
                
        return True
    
    def _get_offline_data(self, data_type, user_id):
        """Get data from a local file when offline"""
        file_path = f"offline_data/{data_type}/{user_id}.json"
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error reading offline data: {e}")
                return {"current_scene": "start", "error": str(e)}
        else:
            return {"current_scene": "start", "first_time": True}
