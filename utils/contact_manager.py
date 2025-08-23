import json
import os
from datetime import datetime

class ContactManager:
    def __init__(self, storage_file='data/pending_contacts.json'):
        self.storage_file = storage_file
        self.contacts = self.load_contacts()
    
    def load_contacts(self):
        if os.path.exists(self.storage_file):
            with open(self.storage_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_contacts(self):
        with open(self.storage_file, 'w') as f:
            json.dump(self.contacts, f, indent=4)
    
    def add_contact(self, contact):
        """Add a new contact with email_sent=False"""
        contact['email_sent'] = False
        contact['added_date'] = datetime.now().isoformat()
        self.contacts.append(contact)
        self.save_contacts()
    
    def mark_as_sent(self, address):
        """Mark contact as sent and remove it (or set flag)"""
        self.contacts = [c for c in self.contacts if c.get('address') != address]
        self.save_contacts()
    
    def mark_contact_sent(self, email):
        """Mark contact as sent by email address"""
        for contact in self.contacts:
            if contact.get('owner_email') == email:
                contact['email_sent'] = True
                contact['sent_date'] = datetime.now().isoformat()
                break
        self.save_contacts()
    
    def delete_contact(self, address):
        """Manually delete a contact by address"""
        self.contacts = [c for c in self.contacts if c.get('address') != address]
        self.save_contacts()
    
    def get_pending_contacts(self):
        """Get contacts where email_sent=False"""
        return [c for c in self.contacts if not c.get('email_sent', True)]
    
    def get_all_contacts(self):
        """Get all contacts"""
        return self.contacts 
    
    def get_statistics(self):
        """Get statistics about contacts"""
        total = len(self.contacts)
        pending = len([c for c in self.contacts if not c.get('email_sent', False)])
        sent = len([c for c in self.contacts if c.get('email_sent', False)])
        
        return {
            'total_contacts': total,
            'pending_contacts': pending,
            'sent_contacts': sent,
            'sent_percentage': (sent / total * 100) if total > 0 else 0
        }
    
    def export_to_csv(self, filename='data/contacts_export.csv'):
        """Export all contacts to CSV file"""
        import pandas as pd
        import os
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        df = pd.DataFrame(self.contacts)
        df.to_csv(filename, index=False)
        return filename
    
    def clear_sent_contacts(self):
        """Remove all contacts that have been sent (to free up storage)"""
        original_count = len(self.contacts)
        self.contacts = [c for c in self.contacts if not c.get('email_sent', False)]
        removed_count = original_count - len(self.contacts)
        self.save_contacts()
        return removed_count 