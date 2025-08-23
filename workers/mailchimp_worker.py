from PySide6.QtCore import QThread, Signal
import time
import requests
import json
import os
from datetime import datetime, timedelta
from utils.contact_manager import ContactManager

class MailchimpWorker(QThread):
    """Worker for creating Mailchimp lists AFTER BatchData processing is complete"""
    log_signal = Signal(str)
    progress_signal = Signal(int, int)  # current, total
    finished_signal = Signal(dict)  # results
    
    def __init__(self, consolidated_contacts, mailchimp_api_key=None):
        super().__init__()
        self.consolidated_contacts = consolidated_contacts
        self.stop_flag = False
        
        # Initialize ContactManager for tracking sent emails
        self.contact_manager = ContactManager()
        
        # Mailchimp configuration
        self.api_key = mailchimp_api_key or os.getenv('MAILCHIMP_API_KEY')
        self.server_prefix = os.getenv('MAILCHIMP_SERVER_PREFIX', 'us17')
        
        if not self.api_key:
            self.log_signal.emit("[Mailchimp] ❌ MAILCHIMP_API_KEY not set in environment")
            return
            
        self.base_url = f"https://{self.server_prefix}.api.mailchimp.com/3.0"
        self.auth = ('anystring', self.api_key)
    
    def run(self):
        """Create Mailchimp lists and upload contacts"""
        try:
            if not self.api_key:
                self.log_signal.emit("[Mailchimp] Cannot proceed without API key")
                self.finished_signal.emit({})
                return
            
            self.log_signal.emit("[Mailchimp] Starting Mailchimp list creation and contact upload...")
            
            if not self.consolidated_contacts:
                self.log_signal.emit("[Mailchimp] No contacts to process")
                self.finished_signal.emit({})
                return
            
            # Clean up old lists first to avoid hitting limits
            self.log_signal.emit("[Mailchimp] Cleaning up old lists...")
            self.cleanup_old_lists()
            
            # Separate contacts by fiber availability
            fiber_contacts = []
            no_fiber_contacts = []
            
            for contact in self.consolidated_contacts:
                if contact.get('fiber_available', False):
                    fiber_contacts.append(contact)
                else:
                    no_fiber_contacts.append(contact)
            
            self.log_signal.emit(f"[Mailchimp] Found {len(fiber_contacts)} fiber contacts, {len(no_fiber_contacts)} no-fiber contacts")
            
            results = {
                'fiber_list_created': False,
                'no_fiber_list_created': False,
                'fiber_contacts_uploaded': 0,
                'no_fiber_contacts_uploaded': 0,
                'errors': []
            }
            
            # Create fiber available list
            if fiber_contacts:
                self.log_signal.emit("[Mailchimp] Creating fiber available list...")
                fiber_list_id = self.create_mailchimp_list("AT&T Fiber Available", True)
                
                if fiber_list_id:
                    results['fiber_list_created'] = True
                    self.log_signal.emit(f"[Mailchimp] Created fiber list with ID: {fiber_list_id}")
                    
                    # Upload fiber contacts
                    uploaded = self.upload_contacts_to_list(fiber_list_id, fiber_contacts, True)
                    results['fiber_contacts_uploaded'] = uploaded
                else:
                    results['errors'].append("Failed to create fiber available list")
            
            # Create no fiber list
            if no_fiber_contacts:
                self.log_signal.emit("[Mailchimp] Creating no fiber list...")
                no_fiber_list_id = self.create_mailchimp_list("No AT&T Fiber", False)
                
                if no_fiber_list_id:
                    results['no_fiber_list_created'] = True
                    self.log_signal.emit(f"[Mailchimp] Created no-fiber list with ID: {no_fiber_list_id}")
                    
                    # Upload no-fiber contacts
                    uploaded = self.upload_contacts_to_list(no_fiber_list_id, no_fiber_contacts, False)
                    results['no_fiber_contacts_uploaded'] = uploaded
                else:
                    results['errors'].append("Failed to create no fiber list")
            
            # Save results to file
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            results_file = f'mailchimp_results_{timestamp}.json'
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            self.log_signal.emit(f"[Mailchimp] ✅ Completed Mailchimp processing")
            self.log_signal.emit(f"[Mailchimp] Results saved to {results_file}")
            
            self.finished_signal.emit(results)
            
        except Exception as e:
            self.log_signal.emit(f"[ERROR] Mailchimp processing failed: {e}")
            self.finished_signal.emit({})
    
    def cleanup_old_lists(self):
        """Delete old Mailchimp lists to avoid hitting limits"""
        try:
            # Get all lists
            response = requests.get(f"{self.base_url}/lists", auth=self.auth)
            
            if response.status_code == 200:
                lists_data = response.json()
                lists = lists_data.get('lists', [])
                
                # Find lists older than 7 days
                cutoff_date = datetime.now() - timedelta(days=7)
                deleted_count = 0
                
                for list_info in lists:
                    list_name = list_info.get('name', '')
                    created_date_str = list_info.get('date_created', '')
                    
                    # Check if it's our AT&T Fiber list and older than 7 days
                    if ('AT&T Fiber' in list_name or 'No AT&T Fiber' in list_name) and created_date_str:
                        try:
                            created_date = datetime.fromisoformat(created_date_str.replace('Z', '+00:00'))
                            if created_date < cutoff_date:
                                list_id = list_info.get('id')
                                delete_response = requests.delete(f"{self.base_url}/lists/{list_id}", auth=self.auth)
                                if delete_response.status_code == 204:
                                    self.log_signal.emit(f"[Mailchimp] Deleted old list: {list_name}")
                                    deleted_count += 1
                        except Exception as e:
                            self.log_signal.emit(f"[Mailchimp] Error parsing date for list {list_name}: {e}")
                            continue
                
                self.log_signal.emit(f"[Mailchimp] Cleaned up {deleted_count} old lists")
            else:
                self.log_signal.emit(f"[Mailchimp] Error getting lists: {response.status_code}")
                
        except Exception as e:
            self.log_signal.emit(f"[Mailchimp] Error cleaning up lists: {e}")
    
    def create_mailchimp_list(self, list_name, is_fiber_list):
        """Create a new Mailchimp list"""
        try:
            # Add date suffix to list name
            date_suffix = datetime.now().strftime('%Y-%m-%d')
            full_list_name = f"{list_name} - {date_suffix}"
            
            list_data = {
                "name": full_list_name,
                "contact": {
                    "company": "AT&T Fiber Tracker",
                    "address1": "123 Main St",
                    "city": "Wilmington",
                    "state": "NC",
                    "zip": "28401",
                    "country": "US"
                },
                "permission_reminder": "You're receiving this email because you have AT&T fiber availability in your area.",
                "use_archive_bar": True,
                "campaign_defaults": {
                    "from_name": "AT&T Fiber Tracker",
                    "from_email": "noreply@attfibertracker.com",
                    "subject": "AT&T Fiber Availability Update",
                    "language": "en"
                },
                "notify_on_subscribe": "noreply@attfibertracker.com",
                "notify_on_unsubscribe": "noreply@attfibertracker.com",
                "email_type_option": True,
                "visibility": "pub"
            }
            
            response = requests.post(
                f"{self.base_url}/lists",
                auth=self.auth,
                json=list_data
            )
            
            if response.status_code == 200:
                list_info = response.json()
                return list_info['id']
            else:
                self.log_signal.emit(f"[Mailchimp] Error creating list: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_signal.emit(f"[Mailchimp] Exception creating list: {e}")
            return None
    
    def add_merge_fields(self, list_id):
        """Add custom merge fields to the list"""
        try:
            merge_fields = [
                {
                    "tag": "ADDRESS",
                    "name": "Address",
                    "type": "text",
                    "required": False,
                    "default_value": "",
                    "public": True
                },
                {
                    "tag": "FIBER_STATUS",
                    "name": "Fiber Status",
                    "type": "text",
                    "required": False,
                    "default_value": "",
                    "public": True
                },
                {
                    "tag": "PROPERTY_VALUE",
                    "name": "Property Value",
                    "type": "text",
                    "required": False,
                    "default_value": "",
                    "public": True
                }
            ]
            
            for field in merge_fields:
                response = requests.post(
                    f"{self.base_url}/lists/{list_id}/merge-fields",
                    auth=self.auth,
                    json=field
                )
                
                if response.status_code not in [200, 400]:  # 400 means field already exists
                    self.log_signal.emit(f"[Mailchimp] Error adding merge field: {response.status_code}")
                    
        except Exception as e:
            self.log_signal.emit(f"[Mailchimp] Exception adding merge fields: {e}")
    
    def upload_contacts_to_list(self, list_id, contacts, has_fiber):
        """Upload contacts to a Mailchimp list"""
        try:
            self.add_merge_fields(list_id)
            
            uploaded_count = 0
            total_contacts = len(contacts)
            
            for i, contact in enumerate(contacts):
                if self.stop_flag:
                    break
                    
                self.progress_signal.emit(i + 1, total_contacts)
                
                try:
                    # Prepare contact data
                    member_data = {
                        "email_address": contact.get('owner_email', f"contact{i}@example.com"),
                        "status": "subscribed",
                        "merge_fields": {
                            "FNAME": contact.get('owner_name', '').split()[0] if contact.get('owner_name') else '',
                            "LNAME": ' '.join(contact.get('owner_name', '').split()[1:]) if contact.get('owner_name') else '',
                            "ADDRESS": contact.get('address', ''),
                            "FIBER_STATUS": "Available" if has_fiber else "Not Available",
                            "PROPERTY_VALUE": contact.get('property_value', '')
                        }
                    }
                    
                    # Use email as subscriber hash
                    import hashlib
                    email_hash = hashlib.md5(contact.get('owner_email', f"contact{i}@example.com").lower().encode()).hexdigest()
                    
                    response = requests.put(
                        f"{self.base_url}/lists/{list_id}/members/{email_hash}",
                        auth=self.auth,
                        json=member_data
                    )
                    
                    if response.status_code in [200, 201]:
                        uploaded_count += 1
                        self.log_signal.emit(f"[Mailchimp] Uploaded: {contact.get('owner_email', f'contact{i}@example.com')}")
                        # Mark contact as sent in ContactManager
                        self.contact_manager.mark_contact_sent(contact.get('owner_email'))
                    else:
                        self.log_signal.emit(f"[Mailchimp] Failed to upload {contact.get('owner_email', f'contact{i}@example.com')}: {response.status_code}")
                        self.log_signal.emit(f"[Mailchimp] Payload: {json.dumps(member_data)}")
                        self.log_signal.emit(f"[Mailchimp] Response: {response.text}")
                    
                    # Rate limiting
                    time.sleep(0.1)
                    
                except Exception as e:
                    self.log_signal.emit(f"[Mailchimp] Error uploading contact: {e}")
                    continue
            
            self.log_signal.emit(f"[Mailchimp] Uploaded {uploaded_count}/{total_contacts} contacts to list {list_id}")
            return uploaded_count
            
        except Exception as e:
            self.log_signal.emit(f"[Mailchimp] Exception uploading contacts: {e}")
            return 0
    
    def stop(self):
        """Stop the worker"""
        self.stop_flag = True 

    def upload_contact(self, contact, list_id):
        """Upload a single contact to Mailchimp and log detailed errors"""
        import requests
        import json
        try:
            url = f"https://usX.api.mailchimp.com/3.0/lists/{list_id}/members"
            payload = {
                "email_address": contact.get("email"),
                "status": "subscribed",
                "merge_fields": {
                    "FNAME": contact.get("first_name", ""),
                    "LNAME": contact.get("last_name", ""),
                    "ADDRESS": contact.get("address", "")
                }
            }
            headers = {
                "Authorization": f"apikey {self.api_key}",
                "Content-Type": "application/json"
            }
            response = requests.post(url, headers=headers, data=json.dumps(payload))
            if response.status_code == 200 or response.status_code == 201:
                self.log_signal.emit(f"[Mailchimp] Uploaded {contact.get('email')}")
                return True
            else:
                self.log_signal.emit(f"[Mailchimp] Failed to upload {contact.get('email')}: {response.status_code}")
                self.log_signal.emit(f"[Mailchimp] Payload: {json.dumps(payload)}")
                self.log_signal.emit(f"[Mailchimp] Response: {response.text}")
                return False
        except Exception as e:
            self.log_signal.emit(f"[Mailchimp] Exception uploading {contact.get('email')}: {e}")
            return False 