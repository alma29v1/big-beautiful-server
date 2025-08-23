"""Service for getting contact information from Bach."""

import requests
from typing import Dict, List, Optional
from ..config import BACH_API_KEY

class BachService:
    """Service for interacting with Bach's API."""
    
    def __init__(self):
        self.api_key = BACH_API_KEY
        
    def get_contact_info(self, address: str) -> Dict:
        """Get contact information for a property address.
        
        Args:
            address: Property address to look up
            
        Returns:
            Dict containing contact information if found
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # Format payload for Bach API
            payload = {
                'address': address,
                'include_contact_info': True
            }
            
            # Make request to Bach API
            response = requests.post(
                'https://api.bach.com/v1/property/search',
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Extract contact information
            contact_info = {
                'address': address,
                'owner_name': data.get('owner', {}).get('name'),
                'owner_phone': data.get('owner', {}).get('phone'),
                'owner_email': data.get('owner', {}).get('email'),
                'mailing_address': data.get('owner', {}).get('mailing_address')
            }
            
            return contact_info
            
        except Exception as e:
            print(f"Error getting Bach contact info for {address}: {str(e)}")
            return {
                'address': address,
                'error': str(e)
            } 