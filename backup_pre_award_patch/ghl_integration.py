import os
from typing import Optional, Dict, Any
from logger_utils import logger

GHL_API_KEY = os.getenv('GHL_API_KEY', '')
GHL_LOCATION_ID = os.getenv('GHL_LOCATION_ID', '')
GHL_API_URL = 'https://rest.gohighlevel.com/v1'

async def lookup_contact(email: str) -> Optional[Dict[str, Any]]:
    try:
        import requests
        
        headers = {
            'Authorization': f'Bearer {GHL_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        params = {
            'email': email,
            'locationId': GHL_LOCATION_ID
        }
        
        response = requests.get(
            f'{GHL_API_URL}/contacts/',
            headers=headers,
            params=params,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            contacts = data.get('contacts', [])
            if contacts:
                logger.info(f"Contact found for email: {email}")
                return contacts[0]
            else:
                logger.info(f"No contact found for email: {email}")
                return None
        else:
            logger.error(f"GHL API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error looking up contact: {str(e)}")
        return None

async def add_tag_to_contact(contact_id: str, tag: str) -> bool:
    try:
        import requests
        
        headers = {
            'Authorization': f'Bearer {GHL_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'tags': [tag]
        }
        
        response = requests.put(
            f'{GHL_API_URL}/contacts/{contact_id}',
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            logger.info(f"Tag '{tag}' added to contact {contact_id}")
            return True
        else:
            logger.error(f"Failed to add tag: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error adding tag to contact: {str(e)}")
        return False

async def has_freemium_tag(contact: Dict[str, Any]) -> bool:
    if not contact:
        return False
    
    tags = contact.get('tags', [])
    return 'Freemium-Used' in tags

async def create_contact(email: str, name: str = '') -> Optional[Dict[str, Any]]:
    try:
        import requests
        
        headers = {
            'Authorization': f'Bearer {GHL_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'email': email,
            'locationId': GHL_LOCATION_ID
        }
        
        if name:
            payload['name'] = name
        
        response = requests.post(
            f'{GHL_API_URL}/contacts/',
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            contact = response.json().get('contact', {})
            logger.info(f"Contact created for email: {email}")
            return contact
        else:
            logger.error(f"Failed to create contact: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error creating contact: {str(e)}")
        return None
