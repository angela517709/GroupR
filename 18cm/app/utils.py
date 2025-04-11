import os
import json
from datetime import datetime
from flask import current_app

def save_user_profile(user_data):
    """Save user profile data from iAM Smart to profiles.json"""
    try:
        profiles_path = os.path.join(current_app.root_path, 'data', 'profiles.json')
        
        # Create file if it doesn't exist
        if not os.path.exists(profiles_path):
            with open(profiles_path, 'w', encoding='utf-8') as f:
                json.dump({"profiles": []}, f)
        
        # Read existing profiles
        with open(profiles_path, 'r', encoding='utf-8') as f:
            profiles = json.load(f)
        
        # Format user data for profile
        new_profile = {
            "id": user_data['idNo']['Identification'],
            "personal_info": {
                "name": user_data['enName']['UnstructuredName'],
                "idNo": f"{user_data['idNo']['Identification']}{user_data['idNo']['CheckDigit']}",
                "birthDate": user_data['birthDate'],
                "gender": user_data['gender']
            }
        }
        
        # Update existing or add new profile
        profile_exists = False
        for i, profile in enumerate(profiles['profiles']):
            if profile['id'] == new_profile['id']:
                profiles['profiles'][i] = new_profile
                profile_exists = True
                break
                
        if not profile_exists:
            profiles['profiles'].append(new_profile)
        
        # Save updated profiles
        with open(profiles_path, 'w', encoding='utf-8') as f:
            json.dump(profiles, f, indent=2, ensure_ascii=False)
            
        return True
        
    except Exception as e:
        print(f"Error saving profile: {e}")
        return False

def get_user_profile(user_id):
    """Get user profile data from profiles.json"""
    try:
        profiles_path = os.path.join(current_app.root_path, 'data', 'profiles.json')
        
        with open(profiles_path, 'r', encoding='utf-8') as f:
            profiles = json.load(f)
            return next(
                (p for p in profiles['profiles'] if p['id'] == user_id),
                None
            )
            
    except Exception as e:
        print(f"Error loading profile: {e}")
        return None