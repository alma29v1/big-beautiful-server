
"""
Enhanced Email Scheduling Service - Send ADT emails first, AT&T emails next day
"""

import os
import json
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict

class EmailSchedulingService:
    """Handles sequential email sending to avoid customer email conflicts"""
    
    def __init__(self):
        self.schedule_file = "data/email_schedule.json"
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """Ensure data directory exists"""
        os.makedirs("data", exist_ok=True)
    
    def schedule_staggered_campaigns(self, contacts: List[Dict], campaign_configs: Dict) -> Dict:
        """
        Schedule campaigns with staggered delivery:
        - Day 1: ADT emails to all customers
        - Day 2: AT&T Fiber emails to fiber-available customers only
        """
        
        print("📅 Creating staggered email schedule...")
        
        # Separate contacts by fiber availability
        fiber_contacts = [c for c in contacts if c.get('fiber_available', False)]
        all_contacts = contacts
        
        # Create schedule
        schedule = {
            'created_date': datetime.now().isoformat(),
            'total_contacts': len(all_contacts),
            'fiber_contacts': len(fiber_contacts),
            'campaigns': []
        }
        
        # Day 1: AT&T Fiber Campaign (Fiber-available customers only)
        att_campaign = {
            'campaign_id': f"att_fiber_{datetime.now().strftime('%Y%m%d')}",
            'campaign_type': 'AT&T Fiber',
            'send_date': datetime.now().strftime('%Y-%m-%d'),
            'send_time': '09:00',  # 9 AM
            'recipients': len(fiber_contacts),
            'target_audience': 'Fiber-available properties only',
            'subject_lines': [
                'Lightning-Fast Fiber Internet Available at Your Address!',
                'AT&T Fiber Confirmed Available - Upgrade Today',
                'High-Speed Internet Now Ready for Installation'
            ],
            'priority': 'High',
            'contacts': fiber_contacts,
            'notes': 'Send to fiber customers FIRST - strike while iron is hot!'
        }
        
        # Day 2: ADT Security Campaign (ALL customers)
        tomorrow = datetime.now() + timedelta(days=1)
        adt_campaign = {
            'campaign_id': f"adt_security_{tomorrow.strftime('%Y%m%d')}",
            'campaign_type': 'ADT Security',
            'send_date': tomorrow.strftime('%Y-%m-%d'),
            'send_time': '10:00',  # 10 AM next day
            'recipients': len(all_contacts),
            'target_audience': 'All property owners',
            'subject_lines': [
                'Enhance Your Home Security Today',
                'Protect Your Family with Professional Monitoring',
                'Free Security Assessment Available'
            ],
            'priority': 'High',
            'contacts': all_contacts,
            'notes': 'Send to ALL customers (including fiber customers from Day 1) - security is universal need'
        }
        
        schedule['campaigns'] = [att_campaign, adt_campaign]
        
        # Save schedule
        with open(self.schedule_file, 'w') as f:
            json.dump(schedule, f, indent=2)
        
        print(f"✅ Schedule created with {len(schedule['campaigns'])} campaigns")
        print(f"📧 Day 1 (Today): AT&T Fiber → {len(fiber_contacts)} contacts (fiber-available only)")
        print(f"📧 Day 2 (Tomorrow): ADT Security → {len(all_contacts)} contacts (ALL customers)")
        print(f"💾 Schedule saved to: {self.schedule_file}")
        
        return schedule
    
    def prevent_duplicate_campaigns(self, contacts: List[Dict]) -> Dict:
        """
        Prevent AI from creating multiple campaigns for the same contact pool
        """
        
        print("🔄 Analyzing contact pool for duplicate prevention...")
        
        # Create unique campaign fingerprint based on contact data
        contact_fingerprint = self.create_contact_fingerprint(contacts)
        
        # Check for existing campaigns with same fingerprint
        existing_campaigns = self.load_existing_campaigns()
        
        duplicate_check = {
            'contact_fingerprint': contact_fingerprint,
            'is_duplicate': False,
            'existing_campaign': None,
            'recommendation': 'proceed'
        }
        
        for campaign in existing_campaigns:
            if campaign.get('contact_fingerprint') == contact_fingerprint:
                duplicate_check['is_duplicate'] = True
                duplicate_check['existing_campaign'] = campaign
                duplicate_check['recommendation'] = 'skip_or_update'
                break
        
        if duplicate_check['is_duplicate']:
            print(f"⚠️  DUPLICATE DETECTED: Same contact pool already has campaigns")
            print(f"📅 Existing campaign: {duplicate_check['existing_campaign']['campaign_id']}")
            print(f"💡 Recommendation: Update existing campaigns instead of creating new ones")
        else:
            print(f"✅ New contact pool - safe to create campaigns")
        
        return duplicate_check
    
    def create_contact_fingerprint(self, contacts: List[Dict]) -> str:
        """Create unique fingerprint for contact pool to detect duplicates"""
        
        # Sort contacts by address to ensure consistent fingerprint
        sorted_addresses = sorted([c.get('address', '') for c in contacts])
        
        # Create hash of address list + count
        import hashlib
        fingerprint_data = f"{len(contacts)}:{','.join(sorted_addresses[:10])}"  # First 10 addresses
        fingerprint = hashlib.md5(fingerprint_data.encode()).hexdigest()[:12]
        
        return fingerprint
    
    def load_existing_campaigns(self) -> List[Dict]:
        """Load existing campaign schedules"""
        
        try:
            if os.path.exists(self.schedule_file):
                with open(self.schedule_file, 'r') as f:
                    data = json.load(f)
                    return data.get('campaigns', [])
        except:
            pass
        
        return []
    
    def export_for_mailchimp(self, schedule: Dict) -> List[str]:
        """Export scheduled campaigns in MailChimp-ready format"""
        
        exported_files = []
        
        for campaign in schedule['campaigns']:
            # Create MailChimp export
            mailchimp_data = {
                'list_name': f"{campaign['campaign_type']} Campaign - {campaign['send_date']}",
                'campaign_settings': {
                    'subject_line': campaign['subject_lines'][0],
                    'from_name': 'Seaside Security',
                    'from_email': 'info@seasidesecurity.com',
                    'to_name': 'Property Owner'
                },
                'send_schedule': {
                    'date': campaign['send_date'],
                    'time': campaign['send_time']
                },
                'contacts': []
            }
            
            # Add contacts
            for contact in campaign['contacts']:
                mailchimp_contact = {
                    'email_address': contact.get('owner_email', ''),
                    'status': 'subscribed',
                    'merge_fields': {
                        'FNAME': contact.get('owner_first_name', ''),
                        'LNAME': contact.get('owner_last_name', ''),
                        'ADDRESS': contact.get('address', ''),
                        'CITY': contact.get('city', ''),
                        'STATE': contact.get('state', ''),
                        'ZIP': contact.get('zip', ''),
                        'PHONE': contact.get('owner_phone', ''),
                        'CAMPAIGN': campaign['campaign_type'],
                        'FIBER': 'Yes' if contact.get('fiber_available') else 'No'
                    }
                }
                
                if mailchimp_contact['email_address']:  # Only include contacts with emails
                    mailchimp_data['contacts'].append(mailchimp_contact)
            
            # Save export file
            filename = f"mailchimp_{campaign['campaign_type'].lower().replace(' ', '_')}_{campaign['send_date']}.json"
            with open(filename, 'w') as f:
                json.dump(mailchimp_data, f, indent=2)
            
            exported_files.append(filename)
            print(f"📤 Exported: {filename} ({len(mailchimp_data['contacts'])} contacts with emails)")
        
        return exported_files

# Example usage
def demo_email_scheduling():
    """Demonstrate the email scheduling system"""
    
    scheduler = EmailSchedulingService()
    
    # Sample contact data (replace with your actual BatchData results)
    sample_contacts = [
        {
            'address': '123 Main St',
            'city': 'Wilmington',
            'state': 'NC',
            'zip': '28401',
            'owner_first_name': 'John',
            'owner_last_name': 'Smith',
            'owner_email': 'john.smith@email.com',
            'owner_phone': '(910) 123-4567',
            'fiber_available': True
        },
        {
            'address': '456 Oak Ave',
            'city': 'Wilmington', 
            'state': 'NC',
            'zip': '28401',
            'owner_first_name': 'Mary',
            'owner_last_name': 'Johnson',
            'owner_email': 'mary.j@email.com',
            'owner_phone': '(910) 234-5678',
            'fiber_available': False
        }
    ]
    
    # Check for duplicates
    duplicate_check = scheduler.prevent_duplicate_campaigns(sample_contacts)
    
    if not duplicate_check['is_duplicate']:
        # Create staggered schedule
        schedule = scheduler.schedule_staggered_campaigns(sample_contacts, {})
        
        # Export for MailChimp
        exported_files = scheduler.export_for_mailchimp(schedule)
        
        print(f"\n🎉 EMAIL SCHEDULING COMPLETE!")
        print(f"📋 Schedule: {scheduler.schedule_file}")
        print(f"📤 MailChimp files: {exported_files}")
    else:
        print(f"\n⏸️  SKIPPING: Duplicate campaign detected")

if __name__ == "__main__":
    demo_email_scheduling()
