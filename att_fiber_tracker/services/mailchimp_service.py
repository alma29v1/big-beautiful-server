import mailchimp_marketing as MailchimpMarketing
from mailchimp_marketing.api_client import ApiClientError
import hashlib
import logging

logger = logging.getLogger(__name__)

class MailchimpService:
    def __init__(self, api_key, server_prefix):
        self.client = MailchimpMarketing.Client()
        self.client.set_config({
            "api_key": api_key,
            "server": server_prefix
        })
        
    def test_connection(self):
        """Test the Mailchimp connection and return available lists."""
        try:
            # Try to get all lists
            response = self.client.lists.get_all_lists()
            lists = response.get("lists", [])
            return {
                "success": True,
                "lists": [{"name": list_info["name"], "id": list_info["id"]} for list_info in lists]
            }
        except ApiClientError as e:
            logger.error(f"Error testing Mailchimp connection: {e.text}")
            return {
                "success": False,
                "error": str(e.text)
            }
        
    def create_lists_if_not_exist(self):
        """Create the fiber and no-fiber lists if they don't exist."""
        try:
            # First, try to get all lists
            response = self.client.lists.get_all_lists()
            existing_lists = {list_info["name"]: list_info["id"] for list_info in response["lists"]}
            
            fiber_list_id = existing_lists.get("AT&T Fiber Available")
            no_fiber_list_id = existing_lists.get("No AT&T Fiber")
            
            # Create fiber available list if it doesn't exist
            if not fiber_list_id:
                fiber_list = self.client.lists.create_list({
                    "name": "AT&T Fiber Available",
                    "permission_reminder": "You are receiving this email because this property has AT&T Fiber available.",
                    "email_type_option": True,
                    "contact": {
                        "company": "AT&T Fiber Tracker",
                        "address1": "123 Main St",
                        "city": "Leland",
                        "state": "NC",
                        "zip": "28451",
                        "country": "US"
                    },
                    "campaign_defaults": {
                        "from_name": "AT&T Fiber Tracker",
                        "from_email": "fiber@example.com",
                        "subject": "AT&T Fiber Available",
                        "language": "en"
                    }
                })
                fiber_list_id = fiber_list["id"]
                logger.info(f"Created Fiber Available list with ID: {fiber_list_id}")
                
                # Add merge fields
                self.add_merge_fields(fiber_list_id)
            
            # Create no fiber list if it doesn't exist
            if not no_fiber_list_id:
                no_fiber_list = self.client.lists.create_list({
                    "name": "No AT&T Fiber",
                    "permission_reminder": "You are receiving this email because this property does not have AT&T Fiber.",
                    "email_type_option": True,
                    "contact": {
                        "company": "AT&T Fiber Tracker",
                        "address1": "123 Main St",
                        "city": "Leland",
                        "state": "NC",
                        "zip": "28451",
                        "country": "US"
                    },
                    "campaign_defaults": {
                        "from_name": "AT&T Fiber Tracker",
                        "from_email": "fiber@example.com",
                        "subject": "No AT&T Fiber Available",
                        "language": "en"
                    }
                })
                no_fiber_list_id = no_fiber_list["id"]
                logger.info(f"Created No Fiber list with ID: {no_fiber_list_id}")
                
                # Add merge fields
                self.add_merge_fields(no_fiber_list_id)
            
            return fiber_list_id, no_fiber_list_id
            
        except ApiClientError as e:
            logger.error(f"Error creating Mailchimp lists: {e.text}")
            raise
    
    def add_merge_fields(self, list_id):
        """Add required merge fields to a list."""
        merge_fields = [
            {"name": "First Name", "tag": "FNAME", "type": "text"},
            {"name": "Last Name", "tag": "LNAME", "type": "text"},
            {"name": "Full Name", "tag": "FULLNAME", "type": "text"},
            {"name": "Phone", "tag": "PHONE", "type": "phone"},
            {"name": "Address", "tag": "ADDRESS", "type": "text"},
            {"name": "Has Fiber", "tag": "HASFIBER", "type": "text"},
            {"name": "Price", "tag": "PRICE", "type": "number"},
            {"name": "Beds", "tag": "BEDS", "type": "number"},
            {"name": "Baths", "tag": "BATHS", "type": "number"},
            {"name": "Square Feet", "tag": "SQFT", "type": "number"}
        ]
        
        for field in merge_fields:
            try:
                self.client.lists.add_list_merge_field(list_id, field)
            except ApiClientError as e:
                if "already exists" not in str(e):
                    raise
    
    def add_to_list(self, list_id, email, first_name="", last_name="", address="", has_fiber=False,
                    price=None, beds=None, baths=None, sqft=None):
        """Add a contact to a Mailchimp list."""
        try:
            subscriber_hash = hashlib.md5(email.lower().encode()).hexdigest()
            
            merge_fields = {
                "FNAME": first_name,
                "LNAME": last_name,
                "FULLNAME": f"{first_name} {last_name}".strip(),
                "ADDRESS": address,
                "HASFIBER": "Yes" if has_fiber else "No"
            }
            
            # Add optional fields if they exist
            if price is not None:
                merge_fields["PRICE"] = price
            if beds is not None:
                merge_fields["BEDS"] = beds
            if baths is not None:
                merge_fields["BATHS"] = baths
            if sqft is not None:
                merge_fields["SQFT"] = sqft
            
            self.client.lists.set_list_member(
                list_id,
                subscriber_hash,
                {
                    "email_address": email,
                    "status_if_new": "subscribed",
                    "merge_fields": merge_fields
                }
            )
            logger.info(f"Successfully added/updated {email} to list {list_id}")
            
        except ApiClientError as e:
            logger.error(f"Error adding contact to Mailchimp: {e.text}")
            raise
    
    def download_list_emails(self, list_id):
        """Download all emails from a Mailchimp list."""
        try:
            logger.info(f"Fetching members from list {list_id}")
            # Get all members from the list
            response = self.client.lists.get_list_members_info(list_id, count=1000)
            members = response.get("members", [])
            logger.info(f"Found {len(members)} members in list {list_id}")
            
            # Extract email addresses and merge fields
            emails = []
            for member in members:
                email_data = {
                    "email": member.get("email_address", ""),
                    "status": member.get("status", ""),
                    "merge_fields": member.get("merge_fields", {}),
                    "last_changed": member.get("last_changed", ""),
                    "timestamp_signup": member.get("timestamp_signup", "")
                }
                emails.append(email_data)
                logger.debug(f"Processed email: {email_data['email']}")
            
            return {
                "success": True,
                "emails": emails,
                "total": len(emails)
            }
            
        except ApiClientError as e:
            logger.error(f"Error downloading emails from Mailchimp list: {e.text}")
            return {
                "success": False,
                "error": str(e.text)
            } 