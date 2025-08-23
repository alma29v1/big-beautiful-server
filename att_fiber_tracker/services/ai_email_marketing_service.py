"""
AI Email Marketing Service - Comprehensive AI-powered email campaign generation
"""

import os
import json
import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from utils.api_cost_tracker import track_activeknocker_usage

logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from config.json"""
    try:
        with open('config/config.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load config.json: {e}")
        return {}

# Load config at module level
CONFIG = load_config()

class CampaignType(Enum):
    """Types of marketing campaigns"""
    FIBER_INTRODUCTION = "fiber_introduction"
    ADT_SECURITY_OFFER = "adt_security_offer"
    COMBINED_SERVICES = "combined_services"
    FOLLOW_UP = "follow_up"
    SEASONAL_PROMOTION = "seasonal_promotion"
    NEIGHBORHOOD_FOCUS = "neighborhood_focus"

class EmailTone(Enum):
    """Email tone options"""
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    URGENT = "urgent"
    INFORMATIVE = "informative"
    CONVERSATIONAL = "conversational"

@dataclass
class ContactProfile:
    """Profile information for personalized emails"""
    name: str
    address: str
    city: str
    state: str
    zip_code: str
    has_fiber: bool = False
    has_adt: bool = False
    property_value: Optional[str] = None
    neighborhood: Optional[str] = None
    email: Optional[str] = None

@dataclass
class CampaignConfig:
    """Configuration for email campaign generation"""
    campaign_type: CampaignType
    tone: EmailTone
    target_audience: str
    company_name: str = "Your Company"
    sender_name: str = "Your Name"
    call_to_action: str = "Contact us today"
    include_statistics: bool = True
    include_testimonials: bool = False
    max_length: int = 500
    personalization_level: str = "high"

class AIEmailMarketingService:
    """Comprehensive AI-powered email marketing service"""
    
    def __init__(self):
        self.openai_api_key = CONFIG.get('openai_api_key')
        self.xai_api_key = CONFIG.get('xai_api_key')
        self.setup_templates()
        
    def setup_templates(self):
        """Setup email templates and prompts"""
        self.campaign_prompts = {
            CampaignType.FIBER_INTRODUCTION: {
                "subject_prompts": [
                    "High-Speed Fiber Internet Now Available in {city}",
                    "Upgrade to Lightning-Fast Fiber in {neighborhood}",
                    "{name}, Fiber Internet Has Arrived!",
                    "Say Goodbye to Slow Internet - Fiber is Here!"
                ],
                "key_points": [
                    "Ultra-fast speeds up to 1 Gig",
                    "Reliable connection for work from home",
                    "Better streaming and gaming experience",
                    "Competitive pricing with no contracts"
                ]
            },
            CampaignType.ADT_SECURITY_OFFER: {
                "subject_prompts": [
                    "Protect Your {city} Home with Advanced Security",
                    "{name}, Enhance Your Home Security Today",
                    "Special Security Offer for {neighborhood} Residents",
                    "Your Home Deserves Better Protection"
                ],
                "key_points": [
                    "24/7 professional monitoring",
                    "Smart home integration",
                    "Mobile app control",
                    "Quick emergency response"
                ]
            }
        }
        
        self.tone_instructions = {
            EmailTone.PROFESSIONAL: "Use formal, business-appropriate language. Be respectful and authoritative.",
            EmailTone.FRIENDLY: "Use warm, approachable language. Be conversational but not overly casual.",
            EmailTone.URGENT: "Create sense of urgency without being pushy. Use action-oriented language.",
            EmailTone.INFORMATIVE: "Focus on facts and benefits. Be educational and helpful.",
            EmailTone.CONVERSATIONAL: "Write like talking to a neighbor. Be casual and relatable."
        }

    def generate_email_campaign(self, contacts: List, config: CampaignConfig) -> Dict:
        """Generate a complete email campaign with personalized emails"""
        try:
            logger.info(f"Generating {config.campaign_type.value} campaign for {len(contacts)} contacts")
            
            # Convert dictionary contacts to ContactProfile objects if needed
            contact_profiles = []
            for contact in contacts:
                if isinstance(contact, dict):
                    # Convert dictionary to ContactProfile
                    profile = ContactProfile(
                        name=contact.get('name', 'Valued Customer'),
                        address=contact.get('address', ''),
                        city=contact.get('city', ''),
                        state=contact.get('state', ''),
                        zip_code=contact.get('zip', ''),
                        has_fiber=contact.get('fiber', 'false').lower() == 'true',
                        has_adt=contact.get('adt', 'false').lower() == 'true',
                        neighborhood=contact.get('neighborhood', ''),
                        email=contact.get('email', '')
                    )
                    contact_profiles.append(profile)
                else:
                    # Already a ContactProfile object
                    contact_profiles.append(contact)
            
            # Generate campaign overview
            campaign_overview = self._generate_campaign_overview(config)
            
            # Generate subject line variations
            subject_lines = self._generate_subject_lines(config, contact_profiles)
            
            # Generate email templates
            email_templates = self._generate_email_templates(config, contact_profiles)
            
            # Generate personalized emails
            personalized_emails = []
            for contact in contact_profiles:
                email = self._generate_personalized_email(contact, config, email_templates)
                personalized_emails.append(email)
            
            # Generate A/B test variations
            ab_test_variations = self._generate_ab_test_variations(config)
            
            # Generate performance predictions
            performance_prediction = self._predict_campaign_performance(config, contact_profiles)
            
            campaign = {
                'campaign_id': f"campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'created_at': datetime.now().isoformat(),
                'config': {
                    'type': config.campaign_type.value,
                    'tone': config.tone.value,
                    'target_audience': config.target_audience,
                    'company_name': config.company_name,
                    'sender_name': config.sender_name
                },
                'overview': campaign_overview,
                'subject_lines': subject_lines,
                'templates': email_templates,
                'personalized_emails': personalized_emails,
                'ab_test_variations': ab_test_variations,
                'performance_prediction': performance_prediction,
                'total_recipients': len(contact_profiles),
                'estimated_cost': self._calculate_campaign_cost(len(contact_profiles))
            }
            
            # Save campaign
            self._save_campaign(campaign)
            
            return campaign
            
        except Exception as e:
            logger.error(f"Error generating email campaign: {e}")
            return {}

    def _generate_campaign_overview(self, config: CampaignConfig) -> Dict:
        """Generate campaign overview and strategy"""
        prompt = f"""
        Create a comprehensive email marketing campaign overview for:
        
        Campaign Type: {config.campaign_type.value}
        Tone: {config.tone.value}
        Target Audience: {config.target_audience}
        Company: {config.company_name}
        
        Provide:
        1. Campaign objective and goals
        2. Target audience analysis
        3. Key messaging strategy
        4. Expected outcomes
        5. Success metrics to track
        
        Format as JSON with clear sections.
        """
        
        response = self._call_ai_api(prompt)
        try:
            return json.loads(response)
        except:
            return {"overview": response}

    def _generate_subject_lines(self, config: CampaignConfig, contacts: List[ContactProfile]) -> List[str]:
        """Generate multiple subject line variations"""
        cities = list(set([c.city for c in contacts[:5]]))
        neighborhoods = list(set([c.neighborhood for c in contacts[:5] if c.neighborhood]))
        
        base_prompts = self.campaign_prompts.get(config.campaign_type, {}).get("subject_prompts", [])
        
        prompt = f"""
        Generate 10 compelling email subject lines for a {config.campaign_type.value} campaign.
        
        Tone: {config.tone.value}
        Target cities: {', '.join(cities)}
        Sample neighborhoods: {', '.join(neighborhoods)}
        
        Requirements:
        - Keep under 50 characters
        - Create urgency and interest
        - Include personalization opportunities
        - Avoid spam trigger words
        - {self.tone_instructions[config.tone]}
        
        Return as a JSON array of strings.
        """
        
        response = self._call_ai_api(prompt)
        try:
            return json.loads(response)
        except:
            return base_prompts

    def _generate_email_templates(self, config: CampaignConfig, contacts: List[ContactProfile]) -> Dict:
        """Generate email templates for different scenarios"""
        campaign_info = self.campaign_prompts.get(config.campaign_type, {})
        key_points = campaign_info.get("key_points", [])
        
        prompt = f"""
        Create 3 email template variations for a {config.campaign_type.value} campaign:
        
        Template Requirements:
        - Tone: {config.tone.value} - {self.tone_instructions[config.tone]}
        - Length: {config.max_length} words maximum
        - Include personalization placeholders: {{name}}, {{city}}, {{address}}, {{neighborhood}}
        - Strong call-to-action: {config.call_to_action}
        - Company: {config.company_name}
        - Sender: {config.sender_name}
        
        Key points to include:
        {chr(10).join(f"- {point}" for point in key_points)}
        
        Create:
        1. "standard" - Balanced approach
        2. "benefit_focused" - Emphasizes benefits and value
        3. "urgency_driven" - Creates time-sensitive appeal
        
        Format as JSON with template names as keys and email content as values.
        Include separate "subject" and "body" for each template.
        """
        
        response = self._call_ai_api(prompt)
        try:
            return json.loads(response)
        except:
            return {"standard": {"subject": "Great Opportunity", "body": response}}

    def _generate_personalized_email(self, contact: ContactProfile, config: CampaignConfig, templates: Dict) -> Dict:
        """Generate a personalized email for a specific contact"""
        template_name = self._select_best_template(contact, config)
        template = templates.get(template_name, templates.get("standard", {}))
        
        prompt = f"""
        Personalize this email template for:
        
        Contact: {contact.name}
        Address: {contact.address}, {contact.city}, {contact.state}
        Has Fiber: {contact.has_fiber}
        Has ADT: {contact.has_adt}
        Neighborhood: {contact.neighborhood or "N/A"}
        
        Template:
        Subject: {template.get('subject', '')}
        Body: {template.get('body', '')}
        
        Personalization Instructions:
        - Replace all placeholders with actual contact information
        - Add 1-2 sentences specific to their location/situation
        - Adjust messaging based on their current services
        - Keep the same tone and structure
        - {self.tone_instructions[config.tone]}
        
        Return as JSON with "subject" and "body" keys.
        """
        
        response = self._call_ai_api(prompt)
        try:
            personalized = json.loads(response)
        except:
            personalized = {"subject": template.get('subject', ''), "body": response}
        
        return {
            "contact_name": contact.name,
            "contact_email": contact.email,
            "template_used": template_name,
            "subject": personalized.get("subject", ""),
            "body": personalized.get("body", ""),
            "personalization_score": self._calculate_personalization_score(contact, personalized)
        }

    def _generate_ab_test_variations(self, config: CampaignConfig) -> Dict:
        """Generate A/B test variations for the campaign"""
        prompt = f"""
        Create A/B test variations for a {config.campaign_type.value} email campaign:
        
        Generate 2 distinct approaches:
        
        Version A: {config.tone.value} tone, focus on {config.call_to_action}
        Version B: Alternative tone and approach
        
        For each version provide:
        1. Subject line
        2. Email body (max {config.max_length} words)
        3. Call-to-action button text
        4. Key differentiating factor
        
        Format as JSON with "version_a" and "version_b" keys.
        """
        
        response = self._call_ai_api(prompt)
        try:
            return json.loads(response)
        except:
            return {"version_a": {"subject": "Test A"}, "version_b": {"subject": "Test B"}}

    def _predict_campaign_performance(self, config: CampaignConfig, contacts: List[ContactProfile]) -> Dict:
        """Predict campaign performance metrics"""
        base_open_rate = {
            CampaignType.FIBER_INTRODUCTION: 0.22,
            CampaignType.ADT_SECURITY_OFFER: 0.18,
            CampaignType.COMBINED_SERVICES: 0.25,
            CampaignType.FOLLOW_UP: 0.15,
            CampaignType.SEASONAL_PROMOTION: 0.28,
            CampaignType.NEIGHBORHOOD_FOCUS: 0.30
        }.get(config.campaign_type, 0.20)
        
        base_click_rate = base_open_rate * 0.15
        base_conversion_rate = base_click_rate * 0.05
        
        personalization_boost = {
            "low": 1.0,
            "medium": 1.15,
            "high": 1.30
        }.get(config.personalization_level, 1.0)
        
        total_recipients = len(contacts)
        predicted_opens = int(total_recipients * base_open_rate * personalization_boost)
        predicted_clicks = int(predicted_opens * 0.15)
        predicted_conversions = int(predicted_clicks * 0.05)
        
        return {
            "total_recipients": total_recipients,
            "predicted_opens": predicted_opens,
            "predicted_clicks": predicted_clicks,
            "predicted_conversions": predicted_conversions
        }

    def _calculate_campaign_cost(self, total_recipients: int) -> float:
        """Calculate estimated cost for the campaign"""
        # This is a placeholder. In a real application, you'd integrate with a cost tracking API.
        # For now, we'll return a dummy value.
        return total_recipients * 0.0001 # Example: $0.0001 per recipient

    def _save_campaign(self, campaign: Dict):
        """Save the generated campaign to a file"""
        try:
            with open(f"campaigns/{campaign['campaign_id']}.json", "w") as f:
                json.dump(campaign, f, indent=4)
            logger.info(f"Campaign {campaign['campaign_id']} saved successfully.")
        except Exception as e:
            logger.error(f"Error saving campaign {campaign['campaign_id']}: {e}")

    def _call_ai_api(self, prompt: str) -> str:
        """Generic method to call the AI API"""
        if not self.openai_api_key:
            raise ValueError("OpenAI API key not configured.")
        
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "gpt-4", # Example model, adjust as needed
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling AI API: {e}")
            raise

    def _select_best_template(self, contact: ContactProfile, config: CampaignConfig) -> str:
        """Select the most appropriate template based on contact profile"""
        # This is a simplified example. In a real application, you'd use more sophisticated logic
        # based on the contact's specific needs, preferences, and previous interactions.
        if contact.has_fiber and contact.has_adt:
            return "combined_services"
        elif contact.has_fiber:
            return "fiber_introduction"
        elif contact.has_adt:
            return "adt_security_offer"
        else:
            return "standard" # Fallback to a general template

    def _calculate_personalization_score(self, contact: ContactProfile, personalized_email: Dict) -> float:
        """Calculate a score for how well the email is personalized"""
        # This is a placeholder. In a real application, you'd use a more sophisticated
        # machine learning model to predict engagement based on personalized content.
        score = 0
        if personalized_email["subject"] != "Great Opportunity":
            score += 1
        if personalized_email["body"] != "Great Opportunity":
            score += 1
        if contact.name in personalized_email["subject"]:
            score += 1
        if contact.name in personalized_email["body"]:
            score += 1
        if contact.address in personalized_email["body"]:
            score += 1
        if contact.city in personalized_email["body"]:
            score += 1
        if contact.state in personalized_email["body"]:
            score += 1
        if contact.zip_code in personalized_email["body"]:
            score += 1
        if contact.neighborhood in personalized_email["body"]:
            score += 1
        if contact.email in personalized_email["body"]:
            score += 1
        return score / 10.0 # Normalize score 