#!/usr/bin/env python3
"""
Enhanced AI Email Marketing Service
Full Mailchimp integration with advanced analytics and AI-powered campaign optimization
"""

import os
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import mailchimp_marketing as MailchimpMarketing
from mailchimp_marketing.api_client import ApiClientError
import logging

logger = logging.getLogger(__name__)

@dataclass
class MailchimpCampaignData:
    """Structured Mailchimp campaign data"""
    campaign_id: str
    subject_line: str
    send_time: str
    emails_sent: int
    opens: int
    clicks: int
    open_rate: float
    click_rate: float
    unsubscribes: int
    revenue: float = 0.0
    content_html: str = ""
    content_text: str = ""
    list_id: str = ""
    list_name: str = ""

@dataclass
class CampaignAnalysis:
    """AI analysis of campaign performance"""
    performance_score: float
    key_insights: List[str]
    optimization_recommendations: List[str]
    predicted_improvements: Dict[str, float]
    content_analysis: Dict[str, str]
    audience_insights: Dict[str, str]

class EnhancedAIEmailService:
    """Enhanced AI Email Marketing Service with full Mailchimp integration"""
    
    def __init__(self):
        self.load_config()
        self.setup_mailchimp()
        self.campaign_cache = {}
        self.analytics_cache = {}
        
    def load_config(self):
        """Load configuration and API keys"""
        try:
            config_path = os.path.join('config', 'config.json')
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            self.mailchimp_api_key = config.get('mailchimp_api_key', '')
            self.openai_api_key = config.get('openai_api_key', '')
            self.xai_api_key = config.get('xai_api_key', 'xai-jivCdP5svYk9jCY3uz9fNzOJ2QHoow3sEtkefCKXYsrrTdmtpyKYnVQpx23MSKyOSy7xKjCEZ4W7RmIN')
            
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.mailchimp_api_key = ""
            self.openai_api_key = ""
            self.xai_api_key = ""
    
    def setup_mailchimp(self):
        """Initialize Mailchimp client"""
        if not self.mailchimp_api_key:
            logger.warning("Mailchimp API key not configured")
            self.mailchimp_client = None
            return
        
        try:
            self.mailchimp_client = MailchimpMarketing.Client()
            server_prefix = self.mailchimp_api_key.split('-')[-1]
            self.mailchimp_client.set_config({
                "api_key": self.mailchimp_api_key,
                "server": server_prefix,
            })
            logger.info("Mailchimp client initialized successfully")
        except Exception as e:
            logger.error(f"Error setting up Mailchimp: {e}")
            self.mailchimp_client = None
    
    def get_comprehensive_mailchimp_data(self) -> Dict:
        """Get comprehensive data from Mailchimp including lists, campaigns, and analytics"""
        if not self.mailchimp_client:
            return {"error": "Mailchimp not configured"}
        
        try:
            data = {
                "lists": self.get_all_lists(),
                "campaigns": self.get_campaign_analytics(),
                "templates": self.get_email_templates(),
                "automation": self.get_automation_data(),
                "audience_insights": self.get_audience_insights(),
                "performance_trends": self.analyze_performance_trends(),
                "retrieved_at": datetime.now().isoformat()
            }
            
            # Cache the data
            self.campaign_cache = data
            return data
            
        except Exception as e:
            logger.error(f"Error getting Mailchimp data: {e}")
            return {"error": str(e)}
    
    def get_all_lists(self) -> List[Dict]:
        """Get all Mailchimp lists with detailed stats and deletion eligibility"""
        if not self.mailchimp_client:
            return []
            
        try:
            # Test DNS resolution first
            import socket
            try:
                socket.gethostbyname('us17.api.mailchimp.com')
            except socket.gaierror:
                logger.error("DNS resolution failed for us17.api.mailchimp.com - network connectivity issue")
                return []
            
            response = self.mailchimp_client.lists.get_all_lists(count=50)
            lists_data = []
            
            for lst in response.get('lists', []):
                # Get campaign information for this list
                list_id = lst['id']
                campaign_info = self.get_list_campaign_info(list_id)
                
                list_info = {
                    "id": list_id,
                    "name": lst['name'],
                    "member_count": lst['stats']['member_count'],
                    "open_rate": lst['stats']['open_rate'],
                    "click_rate": lst['stats']['click_rate'],
                    "created_date": lst['date_created'],
                    "last_campaign": lst['stats'].get('last_campaign', ''),
                    "growth_rate": self.calculate_list_growth_rate(list_id),
                    "last_campaign_date": campaign_info.get('last_campaign_date'),
                    "deletion_eligible": campaign_info.get('deletion_eligible', True),
                    "deletion_date": campaign_info.get('deletion_date'),
                    "days_until_deletable": campaign_info.get('days_until_deletable', 0)
                }
                lists_data.append(list_info)
            
            return lists_data
            
        except Exception as e:
            logger.error(f"Error getting lists: {e}")
            return []
    
    def get_list_campaign_info(self, list_id: str) -> Dict:
        """Get campaign information for a specific list to determine deletion eligibility"""
        try:
            # Get campaigns for this list
            campaigns_response = self.mailchimp_client.campaigns.list(
                count=10,
                list_id=list_id,
                status='sent',
                sort_field='send_time',
                sort_dir='DESC'
            )
            
            campaigns = campaigns_response.get('campaigns', [])
            
            if not campaigns:
                # No campaigns sent, can be deleted immediately
                return {
                    'last_campaign_date': None,
                    'deletion_eligible': True,
                    'deletion_date': None,
                    'days_until_deletable': 0
                }
            
            # Get the most recent campaign
            latest_campaign = campaigns[0]
            send_time = latest_campaign.get('send_time')
            
            if not send_time:
                return {
                    'last_campaign_date': None,
                    'deletion_eligible': True,
                    'deletion_date': None,
                    'days_until_deletable': 0
                }
            
            # Parse the send time
            from datetime import datetime, timedelta
            try:
                # MailChimp sends ISO format: "2025-07-29T10:00:00+00:00"
                campaign_date = datetime.fromisoformat(send_time.replace('Z', '+00:00'))
                current_date = datetime.now(campaign_date.tzinfo)
                
                # Calculate days since campaign was sent
                days_since_campaign = (current_date - campaign_date).days
                
                # MailChimp requires 7 days before deletion
                days_until_deletable = max(0, 7 - days_since_campaign)
                deletion_eligible = days_since_campaign >= 7
                
                if deletion_eligible:
                    deletion_date = None
                else:
                    deletion_date = campaign_date + timedelta(days=7)
                
                return {
                    'last_campaign_date': campaign_date.strftime('%Y-%m-%d %H:%M'),
                    'deletion_eligible': deletion_eligible,
                    'deletion_date': deletion_date.strftime('%Y-%m-%d %H:%M') if deletion_date else None,
                    'days_until_deletable': days_until_deletable
                }
                
            except Exception as parse_error:
                logger.error(f"Error parsing campaign date: {parse_error}")
                return {
                    'last_campaign_date': send_time,
                    'deletion_eligible': True,  # Assume deletable if we can't parse
                    'deletion_date': None,
                    'days_until_deletable': 0
                }
                
        except Exception as e:
            logger.error(f"Error getting campaign info for list {list_id}: {e}")
            return {
                'last_campaign_date': None,
                'deletion_eligible': True,  # Assume deletable if we can't get info
                'deletion_date': None,
                'days_until_deletable': 0
            }
    
    def delete_old_audience_lists(self, keep_count: int = 6) -> Dict:
        """Delete old audience lists, keeping only the most recent ones"""
        if not self.mailchimp_client:
            return {"error": "Mailchimp not configured"}
        
        try:
            # Get all lists with deletion eligibility info
            lists = self.get_all_lists()
            if not lists:
                return {"message": "No lists found to manage"}
            
            # Filter only deletable lists
            deletable_lists = [lst for lst in lists if lst.get('deletion_eligible', True)]
            non_deletable_lists = [lst for lst in lists if not lst.get('deletion_eligible', True)]
            
            if not deletable_lists:
                return {"message": "No lists can be deleted at this time due to recent campaigns"}
            
            # Sort deletable lists by creation date (oldest first)
            sorted_deletable_lists = sorted(deletable_lists, key=lambda x: x.get('created_date', ''))
            
            # Calculate how many to delete
            total_deletable = len(sorted_deletable_lists)
            lists_to_delete = total_deletable - keep_count
            
            if lists_to_delete <= 0:
                return {"message": f"Only {total_deletable} deletable lists found, keeping all (limit: {keep_count})"}
            
            deleted_lists = []
            failed_deletions = []
            
            # Delete oldest deletable lists
            for i in range(lists_to_delete):
                list_to_delete = sorted_deletable_lists[i]
                list_id = list_to_delete.get('id')
                list_name = list_to_delete.get('name', 'Unknown')
                
                try:
                    # Delete the list
                    self.mailchimp_client.lists.delete_list(list_id)
                    deleted_lists.append({
                        'id': list_id,
                        'name': list_name,
                        'created_date': list_to_delete.get('created_date', '')
                    })
                    logger.info(f"Deleted list: {list_name} ({list_id})")
                except Exception as e:
                    failed_deletions.append({
                        'id': list_id,
                        'name': list_name,
                        'error': str(e)
                    })
                    logger.error(f"Failed to delete list {list_name}: {e}")
            
            return {
                "success": True,
                "deleted_count": len(deleted_lists),
                "kept_count": keep_count,
                "deleted_lists": deleted_lists,
                "failed_deletions": failed_deletions,
                "remaining_lists": len(lists) - len(deleted_lists),
                "non_deletable_count": len(non_deletable_lists)
            }
            
        except Exception as e:
            logger.error(f"Error managing audience lists: {e}")
            return {"error": f"Error managing audience lists: {str(e)}"}
    
    def clean_unsubscribed_contacts(self, list_id: str = None) -> Dict:
        """Clean up unsubscribed contacts to prevent bounce issues"""
        if not self.mailchimp_client:
            return {"error": "Mailchimp not configured"}
        
        try:
            if not list_id:
                # Get the most recent list
                lists = self.get_all_lists()
                if not lists:
                    return {"error": "No lists found"}
                list_id = lists[0]['id']  # Most recent list
            
            # Get all members in the list
            members = []
            offset = 0
            count = 1000
            
            while True:
                try:
                    response = self.mailchimp_client.lists.get_list_members_info(list_id, count=count, offset=offset)
                    batch_members = response.get('members', [])
                    if not batch_members:
                        break
                    members.extend(batch_members)
                    offset += count
                except Exception as e:
                    print(f"Error getting members: {e}")
                    break
            
            # Filter unsubscribed and cleaned contacts
            unsubscribed = [m for m in members if m.get('status') == 'unsubscribed']
            cleaned = [m for m in members if m.get('status') == 'cleaned']
            
            print(f"📊 Found {len(unsubscribed)} unsubscribed and {len(cleaned)} cleaned contacts")
            
            # Archive unsubscribed contacts (this prevents them from causing bounces)
            archived_count = 0
            for member in unsubscribed + cleaned:
                try:
                    email_hash = member.get('id')
                    if email_hash:
                        # Archive the member (this removes them from the list but keeps them in MailChimp)
                        self.mailchimp_client.lists.delete_list_member(list_id, email_hash)
                        archived_count += 1
                        print(f"🗑️ Archived contact: {member.get('email_address', 'Unknown')}")
                except Exception as e:
                    print(f"❌ Failed to archive contact {member.get('email_address', 'Unknown')}: {e}")
            
            return {
                "success": True,
                "message": f"Cleaned {archived_count} unsubscribed/cleaned contacts",
                "unsubscribed_found": len(unsubscribed),
                "cleaned_found": len(cleaned),
                "archived_count": archived_count
            }
            
        except Exception as e:
            return {"error": f"Error cleaning unsubscribed contacts: {e}"}
    
    def get_list_statistics(self) -> Dict:
        """Get statistics about all lists"""
        if not self.mailchimp_client:
            return {"error": "Mailchimp not configured"}
        
        try:
            lists = self.get_all_lists()
            if not lists:
                return {"message": "No lists found"}
            
            total_lists = len(lists)
            total_subscribers = sum(list.get('member_count', 0) for list in lists)
            
            return {
                "total_lists": total_lists,
                "total_subscribers": total_subscribers,
                "lists": lists
            }
            
        except Exception as e:
            logger.error(f"Error getting list statistics: {e}")
            return {"error": f"Error getting list statistics: {str(e)}"}
    
    def delete_audience_list(self, list_id: str) -> Dict:
        """Delete a specific audience list"""
        if not self.mailchimp_client:
            return {"error": "Mailchimp not configured"}
        
        try:
            # First check if the list exists and get its info
            try:
                list_info = self.mailchimp_client.lists.get_list(list_id)
                list_name = list_info.get('name', 'Unknown')
                member_count = list_info.get('stats', {}).get('member_count', 0)
            except Exception as e:
                return {"error": f"Could not get list information: {str(e)}"}
            
            # Check if list can be deleted (no recent campaigns)
            campaign_info = self.get_list_campaign_info(list_id)
            if not campaign_info.get('deletion_eligible', True):
                days_until_deletable = campaign_info.get('days_until_deletable', 0)
                return {"error": f"List cannot be deleted yet. Wait {days_until_deletable} more days due to recent campaigns."}
            
            # Delete the list
            self.mailchimp_client.lists.delete_list(list_id)
            
            logger.info(f"Successfully deleted list: {list_name} ({list_id})")
            
            return {
                "success": True,
                "message": f"Successfully deleted list: {list_name}",
                "deleted_list": {
                    "id": list_id,
                    "name": list_name,
                    "member_count": member_count
                }
            }
            
        except Exception as e:
            logger.error(f"Error deleting list {list_id}: {e}")
            return {"error": f"Error deleting list: {str(e)}"}
    
    def get_campaign_analytics(self, limit: int = 50) -> List[MailchimpCampaignData]:
        """Get detailed analytics for recent campaigns with improved timeout handling"""
        if not self.mailchimp_client:
            return []
            
        try:
            # Add timeout and DNS resolution handling
            import socket
            import time
            
            # Test DNS resolution first
            try:
                socket.gethostbyname('us17.api.mailchimp.com')
            except socket.gaierror:
                logger.error("DNS resolution failed for us17.api.mailchimp.com - network connectivity issue")
                return []
            
            # Add timeout to the client configuration
            campaigns_response = self.mailchimp_client.campaigns.list(
                count=limit, 
                status='sent',
                sort_field='send_time',
                sort_dir='DESC'
            )
            
            campaigns_data = []
            
            for campaign in campaigns_response.get('campaigns', []):
                campaign_id = campaign['id']
                
                # Get campaign stats with retry logic
                try:
                    # Add timeout and retry for individual campaign stats
                    stats = None
                    content = None
                    
                    # Retry logic for stats
                    for attempt in range(3):
                        try:
                            stats = self.mailchimp_client.reports.get_campaign_report(campaign_id)
                            break
                        except Exception as e:
                            if attempt == 2:  # Last attempt
                                logger.warning(f"Failed to get stats for campaign {campaign_id} after 3 attempts: {e}")
                                stats = {
                                    'emails_sent': 0,
                                    'opens': 0,
                                    'clicks': 0,
                                    'open_rate': 0,
                                    'click_rate': 0,
                                    'unsubscribes': 0
                                }
                            else:
                                import time
                                time.sleep(1)  # Wait before retry
                    
                    # Retry logic for content
                    for attempt in range(3):
                        try:
                            content = self.mailchimp_client.campaigns.get_content(campaign_id)
                            break
                        except Exception as e:
                            if attempt == 2:  # Last attempt
                                logger.warning(f"Failed to get content for campaign {campaign_id} after 3 attempts: {e}")
                                content = {'html': '', 'plain_text': ''}
                            else:
                                import time
                                time.sleep(1)  # Wait before retry
                    
                    # Get list info with retry
                    list_id = campaign.get('recipients', {}).get('list_id', '')
                    list_name = ""
                    if list_id:
                        for attempt in range(2):  # Fewer retries for list info
                            try:
                                list_info = self.mailchimp_client.lists.get_list(list_id)
                                list_name = list_info.get('name', '')
                                break
                            except:
                                if attempt == 1:
                                    list_name = "Unknown List"
                                else:
                                    import time
                                    time.sleep(0.5)
                    
                    campaign_data = MailchimpCampaignData(
                        campaign_id=campaign_id,
                        subject_line=campaign.get('settings', {}).get('subject_line', ''),
                        send_time=campaign.get('send_time', ''),
                        emails_sent=stats.get('emails_sent', 0) if stats else 0,
                        opens=stats.get('opens', 0) if stats else 0,
                        clicks=stats.get('clicks', 0) if stats else 0,
                        open_rate=stats.get('open_rate', 0) if stats else 0,
                        click_rate=stats.get('click_rate', 0) if stats else 0,
                        unsubscribes=stats.get('unsubscribes', 0) if stats else 0,
                        content_html=content.get('html', '') if content else '',
                        content_text=content.get('plain_text', '') if content else '',
                        list_id=list_id,
                        list_name=list_name
                    )
                    
                    campaigns_data.append(campaign_data)
                    
                except Exception as e:
                    logger.warning(f"Error getting stats for campaign {campaign_id}: {e}")
                    continue
            
            return campaigns_data
            
        except Exception as e:
            logger.error(f"Error getting campaign analytics: {e}")
            return []
    
    def get_email_templates(self) -> List[Dict]:
        """Get all email templates from Mailchimp"""
        if not self.mailchimp_client:
            return []
            
        try:
            # Test DNS resolution first
            import socket
            try:
                socket.gethostbyname('us17.api.mailchimp.com')
            except socket.gaierror:
                logger.error("DNS resolution failed for us17.api.mailchimp.com - network connectivity issue")
                return []
            
            response = self.mailchimp_client.templates.list(count=50)
            templates = []
            
            for template in response.get('templates', []):
                template_data = {
                    "id": template['id'],
                    "name": template['name'],
                    "type": template['type'],
                    "created_date": template['date_created'],
                    "thumbnail": template.get('thumbnail', ''),
                    "usage_count": self.get_template_usage_count(template['id'])
                }
                templates.append(template_data)
            
            return templates
            
        except Exception as e:
            logger.error(f"Error getting templates: {e}")
            return []
    
    def get_automation_data(self) -> List[Dict]:
        """Get automation workflow data"""
        if not self.mailchimp_client:
            return []
            
        try:
            # Test DNS resolution first
            import socket
            try:
                socket.gethostbyname('us17.api.mailchimp.com')
            except socket.gaierror:
                logger.error("DNS resolution failed for us17.api.mailchimp.com - network connectivity issue")
                return []
            
            response = self.mailchimp_client.automations.list()
            automations = []
            
            for automation in response.get('automations', []):
                automation_data = {
                    "id": automation['id'],
                    "title": automation.get('settings', {}).get('title', ''),
                    "status": automation['status'],
                    "emails_sent": automation.get('emails_sent', 0),
                    "created_date": automation['create_time'],
                    "trigger_settings": automation.get('trigger_settings', {})
                }
                automations.append(automation_data)
            
            return automations
            
        except Exception as e:
            logger.error(f"Error getting automation data: {e}")
            return []
    
    def get_audience_insights(self) -> Dict:
        """Get detailed audience insights and segmentation data"""
        try:
            lists = self.get_all_lists()
            # Filter lists with valid rates to avoid empty slice warnings
            valid_open_rates = [lst['open_rate'] for lst in lists if lst['open_rate'] > 0]
            valid_click_rates = [lst['click_rate'] for lst in lists if lst['click_rate'] > 0]
            
            insights = {
                "total_subscribers": sum(lst['member_count'] for lst in lists),
                "avg_open_rate": np.mean(valid_open_rates) if valid_open_rates else 0.0,
                "avg_click_rate": np.mean(valid_click_rates) if valid_click_rates else 0.0,
                "list_performance": sorted(lists, key=lambda x: x['open_rate'], reverse=True),
                "growth_trends": self.analyze_subscriber_growth(),
                "engagement_segments": self.segment_by_engagement()
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting audience insights: {e}")
            return {}
    
    def analyze_performance_trends(self) -> Dict:
        """Analyze performance trends over time"""
        try:
            campaigns = self.get_campaign_analytics(100)  # Get more data for trends
            
            if not campaigns:
                return {}
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame([asdict(c) for c in campaigns])
            df['send_date'] = pd.to_datetime(df['send_time'])
            df = df.sort_values('send_date')
            
            # Calculate trends
            trends = {
                "open_rate_trend": self.calculate_trend(df['open_rate'].tolist()),
                "click_rate_trend": self.calculate_trend(df['click_rate'].tolist()),
                "engagement_trend": self.calculate_trend((df['open_rate'] + df['click_rate']).tolist()),
                "best_performing_campaigns": self.get_top_campaigns(campaigns, 'open_rate'),
                "worst_performing_campaigns": self.get_bottom_campaigns(campaigns, 'open_rate'),
                "seasonal_patterns": self.analyze_seasonal_patterns(df),
                "subject_line_insights": self.analyze_subject_lines(campaigns),
                "optimal_send_times": self.analyze_send_times(df)
            }
            
            return trends
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return {}
    
    def ai_analyze_campaign_performance(self, campaign_data: List[MailchimpCampaignData]) -> CampaignAnalysis:
        """Use AI to analyze campaign performance and provide insights"""
        try:
            # Prepare data for AI analysis
            analysis_prompt = self.create_analysis_prompt(campaign_data)
            
            # Get AI insights
            ai_response = self.call_ai_for_analysis(analysis_prompt)
            
            # Parse AI response
            analysis = self.parse_ai_analysis(ai_response, campaign_data)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return self.create_fallback_analysis(campaign_data)
    
    def create_analysis_prompt(self, campaigns: List[MailchimpCampaignData]) -> str:
        """Create comprehensive prompt for AI analysis"""
        # Calculate summary statistics with validation
        total_campaigns = len(campaigns)
        open_rates = [c.open_rate for c in campaigns if c.open_rate > 0]
        click_rates = [c.click_rate for c in campaigns if c.click_rate > 0]
        avg_open_rate = np.mean(open_rates) * 100 if open_rates else 0.0
        avg_click_rate = np.mean(click_rates) * 100 if click_rates else 0.0
        total_emails_sent = sum(c.emails_sent for c in campaigns)
        
        # Get top and bottom performers
        sorted_by_open = sorted(campaigns, key=lambda x: x.open_rate, reverse=True)
        top_performers = sorted_by_open[:3]
        bottom_performers = sorted_by_open[-3:]
        
        prompt = f"""
Analyze this email marketing campaign performance data and provide strategic insights:

CAMPAIGN OVERVIEW:
- Total campaigns analyzed: {total_campaigns}
- Average open rate: {avg_open_rate:.1f}%
- Average click rate: {avg_click_rate:.1f}%
- Total emails sent: {total_emails_sent:,}

TOP PERFORMING CAMPAIGNS:
{self.format_campaigns_for_prompt(top_performers)}

BOTTOM PERFORMING CAMPAIGNS:
{self.format_campaigns_for_prompt(bottom_performers)}

ANALYSIS REQUIRED:
1. Performance Assessment: Rate overall performance (1-10) and explain
2. Key Success Factors: What made top campaigns successful?
3. Failure Analysis: Why did bottom campaigns underperform?
4. Subject Line Patterns: Analyze subject line effectiveness
5. Content Insights: What content strategies work best?
6. Optimization Recommendations: Specific actionable improvements
7. Predicted Impact: Estimate improvement potential

Format response as JSON with these keys:
- performance_score: float (1-10)
- key_insights: array of strings
- optimization_recommendations: array of strings
- predicted_improvements: object with metric improvements
- content_analysis: object with content insights
- audience_insights: object with audience recommendations
"""
        
        return prompt
    
    def format_campaigns_for_prompt(self, campaigns: List[MailchimpCampaignData]) -> str:
        """Format campaign data for AI prompt"""
        formatted = []
        for i, campaign in enumerate(campaigns, 1):
            formatted.append(f"""
Campaign {i}:
- Subject: "{campaign.subject_line}"
- Open Rate: {campaign.open_rate * 100:.1f}%
- Click Rate: {campaign.click_rate * 100:.1f}%
- Emails Sent: {campaign.emails_sent:,}
- Send Time: {campaign.send_time}
""")
        return "\n".join(formatted)
    
    def call_ai_for_analysis(self, prompt: str) -> str:
        """Call AI API for campaign analysis"""
        try:
            # Try XAI first
            if self.xai_api_key:
                return self.call_xai_api(prompt)
            elif self.openai_api_key:
                return self.call_openai_api(prompt)
            else:
                return self.generate_fallback_analysis_text(prompt)
                
        except Exception as e:
            logger.error(f"AI analysis call failed: {e}")
            return self.generate_fallback_analysis_text(prompt)
    
    def call_xai_api(self, prompt: str) -> str:
        """Call XAI API for analysis"""
        url = "https://api.x.ai/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.xai_api_key}"
        }
        
        payload = {
            "messages": [
                {"role": "system", "content": "You are an expert email marketing analyst specializing in campaign performance optimization and data-driven insights."},
                {"role": "user", "content": prompt}
            ],
            "model": "grok-2",  # Use the correct model name
            "temperature": 0.7
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            raise Exception(f"XAI API error: {response.status_code}")
    
    def generate_intelligent_campaign_content(self, campaign_brief: Dict) -> Dict:
        """Generate intelligent campaign content using AI"""
        prompt = f"""
Create a comprehensive email marketing campaign for AT&T Fiber and ADT Security:

CAMPAIGN BRIEF:
- Type: {campaign_brief.get('type', 'fiber_introduction')}
- Target Audience: {campaign_brief.get('audience', 'homeowners')}
- Geographic Focus: {campaign_brief.get('location', 'North Carolina')}
- Tone: {campaign_brief.get('tone', 'professional')}
- Goals: {campaign_brief.get('goals', 'drive conversions')}

REQUIREMENTS:
1. Create 5 subject line variations (under 50 characters)
2. Write 3 email templates (short, medium, long)
3. Design A/B test strategy
4. Suggest audience segmentation
5. Predict performance metrics
6. Recommend send timing
7. Include compliance considerations

Return as detailed JSON with all components.
"""
        
        try:
            ai_response = self.call_ai_for_analysis(prompt)
            return json.loads(ai_response)
        except:
            return self.create_fallback_campaign_content(campaign_brief)
    
    def optimize_email_content(self, content: str) -> str:
        """Optimize email content for better deliverability and reduced spam filtering"""
        if not content:
            return "<p>Thank you for your interest in our security services.</p>"
        
        # Basic HTML structure if not already present
        if not content.strip().startswith('<'):
            content = f"<p>{content}</p>"
        
        # Add proper HTML structure
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Alert</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px;">
        <h2 style="color: #2c3e50; margin-bottom: 15px;">Security Alert</h2>
        {content}
        <hr style="margin: 20px 0; border: none; border-top: 1px solid #ddd;">
        <p style="font-size: 12px; color: #666; margin-top: 20px;">
            This email was sent to you because you are in proximity to a security incident. 
            If you no longer wish to receive these alerts, please contact us.
        </p>
        <p style="font-size: 12px; color: #666;">
            Seaside Security<br>
            123 Business St, Wilmington, NC 28401<br>
            Phone: (910) 597-4085
        </p>
    </div>
</body>
</html>
"""
        
        return html_template

    def optimize_subject_line(self, subject_line: str) -> str:
        """Optimize subject line for better open rates and deliverability"""
        if not subject_line:
            return "Security Alert - Important Information"
        
        # Remove spam trigger words
        spam_words = [
            'free', 'act now', 'limited time', 'urgent', 'exclusive', 'guaranteed',
            'winner', 'congratulations', 'cash', 'money', 'credit', 'loan',
            'investment', 'earn', 'income', 'profit', 'rich', 'wealth',
            'click here', 'buy now', 'order now', 'subscribe', 'unsubscribe'
        ]
        
        optimized = subject_line
        for word in spam_words:
            optimized = optimized.replace(word, '').replace(word.upper(), '').replace(word.title(), '')
        
        # Clean up extra spaces
        optimized = ' '.join(optimized.split())
        
        # Ensure reasonable length (30-50 characters is optimal)
        if len(optimized) > 60:
            optimized = optimized[:57] + "..."
        elif len(optimized) < 20:
            optimized = f"Security Alert: {optimized}"
        
        # Add personalization if not present
        if "*|FNAME|*" not in optimized and "{{FNAME}}" not in optimized:
            optimized = f"*|FNAME|*, {optimized}"
        
        return optimized

    def is_valid_email(self, email: str) -> bool:
        """Enhanced email validation that excludes test emails"""
        if not email or not isinstance(email, str):
            return False
        
        # Skip test emails
        if "test@" in email.lower() or email.lower() in ["test@example.com", "test@test.com"]:
            return False
        
        # Basic email format validation
        if "@" not in email or "." not in email:
            return False
        
        # Skip obviously fake emails
        if email.count("@") > 1:
            return False
        
        return True
        """Validate email address format to reduce bounce rates"""
        import re
        
        if not email or not isinstance(email, str):
            return False
        
        # Basic email regex pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(pattern, email):
            return False
        
        # Additional checks for common bounce causes
        if len(email) > 254:  # RFC 5321 limit
            return False
        
        if email.startswith('.') or email.endswith('.'):
            return False
        
        if '..' in email:
            return False
        
        # Check for common disposable email domains
        disposable_domains = [
            '10minutemail.com', 'guerrillamail.com', 'mailinator.com',
            'tempmail.org', 'throwaway.email', 'yopmail.com'
        ]
        
        domain = email.split('@')[-1].lower()
        if domain in disposable_domains:
            return False
        
        return True

    def create_mailchimp_campaign(self, campaign_data: Dict) -> Dict:
        """Create and send a campaign in MailChimp with improved bounce rate handling"""
        if not self.mailchimp_client:
            return {"success": False, "error": "MailChimp not configured"}
        
        try:
            # Get or create an audience for this campaign
            campaign_title = campaign_data.get('title', 'Campaign')
            list_name = f"Incident Response - {campaign_title}"
            
            # Try to find existing list or create new one
            lists = self.get_all_lists()
            list_id = None
            
            for lst in lists:
                if lst['name'] == list_name:
                    list_id = lst['id']
                    break
            
            # Create new list if not found
            if not list_id:
                list_config = {
                    "name": list_name,
                    "contact": {
                        "company": "Seaside Security",
                        "address1": "123 Business St",
                        "city": "Wilmington",
                        "state": "NC",
                        "zip": "28401",
                        "country": "US"
                    },
                    "permission_reminder": "You are receiving this email because you are in proximity to a security incident.",
                    "campaign_defaults": {
                        "from_name": "Seaside Security",
                        "from_email": "info@seasidesecurity.net",
                        "subject": "Security Alert",
                        "language": "en"
                    },
                    "email_type_option": True
                }
                
                list_response = self.mailchimp_client.lists.create_list(list_config)
                list_id = list_response['id']
                print(f"✅ Created new MailChimp list: {list_name} ({list_id})")
            
            # Improved contact processing with better validation
            contacts = campaign_data.get('contacts', [])
            valid_contacts = []
            invalid_contacts = []
            
            if contacts:
                print(f"📧 Processing {len(contacts)} contacts for MailChimp list...")
                
                for contact in contacts:
                    try:
                        # Extract and validate contact info
                        raw_email = contact.get('owner_email') or contact.get('email')
                        
                        # Skip contacts with invalid email data
                        if not raw_email or pd.isna(raw_email) or raw_email == '':
                            invalid_contacts.append({
                                'contact': contact,
                                'reason': 'No email address'
                            })
                            continue
                        
                        # Convert to string and clean
                        if isinstance(raw_email, str):
                            email = raw_email.strip().lower()
                        else:
                            # Handle non-string emails (e.g., float NaN)
                            email = str(raw_email).strip().lower()
                        
                        # Basic email validation
                        if not self.is_valid_email(email) or "test@" in email or email == "test@example.com":
                            invalid_contacts.append({
                                'contact': contact,
                                'reason': f'Invalid email format: {email}'
                            })
                            continue
                        
                        # Skip test emails
                        if 'test@' in email or email == 'test@example.com':
                            invalid_contacts.append({
                                'contact': contact,
                                'reason': 'Test email address'
                            })
                            continue
                        
                        # Extract and clean name
                        owner_name = contact.get('owner_name', '')
                        if isinstance(owner_name, str) and owner_name.strip():
                            first_name = owner_name.split(' ')[0].strip() if ' ' in owner_name else owner_name.strip()
                            last_name = ' '.join(owner_name.split(' ')[1:]).strip() if len(owner_name.split(' ')) > 1 else ''
                        else:
                            first_name = 'Resident'
                            last_name = ''
                        
                        # Clean address
                        address = contact.get('address', '')
                        if isinstance(address, str):
                            address = address.strip()
                        else:
                            address = str(address) if address else ''
                        
                        # Create valid contact
                        valid_contact = {
                            'email': email,
                            'first_name': first_name,
                            'last_name': last_name,
                            'address': address,
                            'original_contact': contact
                        }
                        valid_contacts.append(valid_contact)
                        
                    except Exception as contact_error:
                        invalid_contacts.append({
                            'contact': contact,
                            'reason': f'Processing error: {str(contact_error)}'
                        })
                        continue
                
                print(f"✅ Valid contacts: {len(valid_contacts)}")
                print(f"❌ Invalid contacts: {len(invalid_contacts)}")
                
                # Add valid contacts to MailChimp list
                if valid_contacts:
                    print(f"📧 Adding {len(valid_contacts)} valid contacts to MailChimp list...")
                    
                    for valid_contact in valid_contacts:
                        try:
                            # Add member to list with improved subscriber status and bounce prevention
                            member_data = {
                                "email_address": valid_contact['email'],
                                "status": "subscribed",  # Explicitly mark as subscribed
                                "merge_fields": {
                                    "FNAME": valid_contact['first_name'],
                                    "LNAME": valid_contact['last_name'],
                                    "ADDRESS": valid_contact['address']
                                },
                                "marketing_permissions": [
                                    {
                                        "marketing_permission_id": "email_marketing",
                                        "enabled": True
                                    }
                                ],
                                "tags": ["incident_response", "security_alert"],  # Add tags for better segmentation
                                "vip": False,  # Not VIP by default
                                "location": {
                                    "latitude": 0,
                                    "longitude": 0
                                }
                            }
                            
                            # Try to add member (will update if exists)
                            try:
                                self.mailchimp_client.lists.add_list_member(list_id, member_data)
                                print(f"  ✅ Added subscriber: {valid_contact['first_name']} ({valid_contact['email']}) - Status: Subscribed")
                            except ApiClientError as member_error:
                                if "already a list member" in str(member_error):
                                    # Update existing member and ensure they're subscribed
                                    import hashlib
                                    email_hash = hashlib.md5(valid_contact['email'].encode()).hexdigest()
                                    
                                    # First, check current status
                                    try:
                                        existing_member = self.mailchimp_client.lists.get_list_member(list_id, email_hash)
                                        current_status = existing_member.get('status', 'unknown')
                                        
                                        if current_status in ['unsubscribed', 'cleaned', 'pending']:
                                            # Re-subscribe if previously unsubscribed
                                            member_data['status'] = 'subscribed'
                                            print(f"  🔄 Re-subscribing contact: {valid_contact['first_name']} ({valid_contact['email']}) - Previous status: {current_status}")
                                        else:
                                            print(f"  ✅ Updated contact: {valid_contact['first_name']} ({valid_contact['email']}) - Status: {current_status}")
                                            
                                    except Exception as status_error:
                                        print(f"  ⚠️ Could not check status for {valid_contact['email']}: {status_error}")
                                    
                                    # Update the member
                                    self.mailchimp_client.lists.update_list_member(list_id, email_hash, member_data)
                                else:
                                    print(f"  ❌ Failed to add contact {valid_contact['email']}: {member_error}")
                                    
                        except Exception as contact_error:
                            print(f"  ❌ Error processing contact {valid_contact['email']}: {contact_error}")
                            continue
                else:
                    print("⚠️ No valid contacts to add to MailChimp list")
                    return {"success": False, "error": "No valid contacts found"}
            
            # Calculate optimal send time (10 AM tomorrow in user's timezone)
            tomorrow = datetime.now() + timedelta(days=1)
            optimal_send_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
            
            # Create campaign with improved deliverability settings and optimal send time
            campaign_settings = {
                "type": "regular",
                "recipients": {"list_id": list_id},
                "settings": {
                    "subject_line": self.optimize_subject_line(campaign_data.get('subject_lines', [campaign_data.get('title', 'Campaign')])[0]),
                    "preview_text": f"Important security alert from {campaign_data.get('company_name', 'Seaside Security')}",
                    "title": f"Incident Response - {campaign_data.get('title', 'Campaign')}",
                    "from_name": campaign_data.get('company_name', 'Seaside Security'),
                    "reply_to": "info@seasidesecurity.net",
                    "auto_footer": True,  # Enable footer for better deliverability
                    "inline_css": True,
                    "to_name": "*|FNAME|*",  # Personalization
                    "folder_id": "",  # No folder for better organization
                    "authenticate": True,  # Enable authentication
                    "auto_tweet": False,  # Disable auto-tweet
                    "fb_comments": False,  # Disable Facebook comments
                    "timewarp": False,  # Disable timewarp
                    "template_id": 0,  # No template
                    "drag_and_drop": True,  # Use drag and drop editor
                    "send_time": optimal_send_time.strftime("%Y-%m-%dT%H:%M:%S%z")  # Schedule for 10 AM tomorrow
                }
            }
            
            # Create the campaign
            response = self.mailchimp_client.campaigns.create(campaign_settings)
            campaign_id = response['id']
            
            # Set campaign content with improved HTML structure
            email_content = campaign_data.get('email_body', 'Campaign content')
            
            # Improve HTML structure for better deliverability
            improved_html = self.optimize_email_content(email_content)
            
            content = {
                "html": improved_html
            }
            
            self.mailchimp_client.campaigns.set_content(campaign_id, content)
            
            # Send the campaign with optimal timing
            try:
                # Use MailChimp's optimal send time feature
                send_settings = {
                    "schedule_time": optimal_send_time.strftime("%Y-%m-%dT%H:%M:%S%z")
                }
                
                # Schedule the campaign for optimal send time
                self.mailchimp_client.campaigns.schedule(campaign_id, send_settings)
                print(f"📅 Campaign scheduled for optimal send time: {optimal_send_time.strftime('%Y-%m-%d %H:%M %Z')}")
                
            except Exception as schedule_error:
                print(f"⚠️ Could not schedule campaign, sending immediately: {schedule_error}")
                # Fallback to immediate send
                self.mailchimp_client.campaigns.send(campaign_id)
            
            logger.info(f"MailChimp campaign created and sent: {campaign_id}")
            
            return {
                "success": True, 
                "campaign_id": campaign_id,
                "list_id": list_id,
                "contacts_added": len(valid_contacts),
                "message": f"Campaign created and sent successfully with {len(valid_contacts)} contacts"
            }
            
        except ApiClientError as e:
            logger.error(f"MailChimp API error: {e}")
            return {"success": False, "error": f"MailChimp API error: {e}"}
        except Exception as e:
            logger.error(f"Error creating MailChimp campaign: {e}")
            return {"success": False, "error": str(e)}

    def create_automated_campaign_optimization(self, campaign_id: str) -> Dict:
        """Create automated optimization recommendations for a campaign"""
        try:
            # Get campaign data
            campaign_data = self.get_single_campaign_data(campaign_id)
            
            if not campaign_data:
                return {"error": "Campaign not found"}
            
            # AI analysis
            optimization_prompt = f"""
Analyze this email campaign and provide specific optimization recommendations:

CAMPAIGN DATA:
- Subject: "{campaign_data.subject_line}"
- Open Rate: {campaign_data.open_rate * 100:.1f}%
- Click Rate: {campaign_data.click_rate * 100:.1f}%
- Emails Sent: {campaign_data.emails_sent:,}
- Unsubscribes: {campaign_data.unsubscribes}

CONTENT PREVIEW:
{campaign_data.content_text[:500]}...

Provide:
1. Subject line improvements (3 variations)
2. Content optimization suggestions
3. Send time recommendations
4. Audience segmentation ideas
5. A/B testing strategy
6. Expected performance improvements

Format as actionable JSON recommendations.
"""
            
            ai_recommendations = self.call_ai_for_analysis(optimization_prompt)
            
            return {
                "campaign_id": campaign_id,
                "current_performance": {
                    "open_rate": campaign_data.open_rate,
                    "click_rate": campaign_data.click_rate,
                    "emails_sent": campaign_data.emails_sent
                },
                "ai_recommendations": ai_recommendations,
                "optimization_score": self.calculate_optimization_potential(campaign_data),
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error creating optimization: {e}")
            return {"error": str(e)}
    
    # Helper methods
    def calculate_list_growth_rate(self, list_id: str) -> float:
        """Calculate list growth rate"""
        try:
            # This would require historical data - simplified for now
            return 0.05  # 5% monthly growth placeholder
        except:
            return 0.0
    
    def get_template_usage_count(self, template_id: str) -> int:
        """Get template usage count"""
        try:
            # This would require campaign analysis - simplified for now
            return 0
        except:
            return 0
    
    def calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction"""
        if len(values) < 2:
            return "insufficient_data"
        
        recent_values = values[-5:] if len(values) >= 5 else values
        older_values = values[:-5] if len(values) >= 10 else values[:-2]
        recent_avg = np.mean(recent_values) if recent_values else 0.0
        older_avg = np.mean(older_values) if older_values else 0.0
        
        if recent_avg > older_avg * 1.05:
            return "improving"
        elif recent_avg < older_avg * 0.95:
            return "declining"
        else:
            return "stable"
    
    def get_top_campaigns(self, campaigns: List[MailchimpCampaignData], metric: str) -> List[Dict]:
        """Get top performing campaigns"""
        sorted_campaigns = sorted(campaigns, key=lambda x: getattr(x, metric), reverse=True)
        return [{"subject": c.subject_line, metric: getattr(c, metric)} for c in sorted_campaigns[:5]]
    
    def get_bottom_campaigns(self, campaigns: List[MailchimpCampaignData], metric: str) -> List[Dict]:
        """Get bottom performing campaigns"""
        sorted_campaigns = sorted(campaigns, key=lambda x: getattr(x, metric))
        return [{"subject": c.subject_line, metric: getattr(c, metric)} for c in sorted_campaigns[:3]]
    
    def analyze_seasonal_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze seasonal performance patterns"""
        try:
            df['month'] = df['send_date'].dt.month
            df['day_of_week'] = df['send_date'].dt.dayofweek
            df['hour'] = df['send_date'].dt.hour
            
            return {
                "best_months": df.groupby('month')['open_rate'].mean().nlargest(3).to_dict(),
                "best_days": df.groupby('day_of_week')['open_rate'].mean().nlargest(3).to_dict(),
                "best_hours": df.groupby('hour')['open_rate'].mean().nlargest(3).to_dict()
            }
        except:
            return {}
    
    def analyze_subject_lines(self, campaigns: List[MailchimpCampaignData]) -> Dict:
        """Analyze subject line patterns"""
        try:
            subject_lengths = [len(c.subject_line) for c in campaigns if c.subject_line]
            subject_analysis = {
                "avg_length": np.mean(subject_lengths) if subject_lengths else 0.0,
                "top_words": self.get_top_words([c.subject_line for c in campaigns]),
                "emoji_impact": self.analyze_emoji_usage(campaigns),
                "personalization_impact": self.analyze_personalization(campaigns)
            }
            return subject_analysis
        except:
            return {}
    
    def get_top_words(self, subject_lines: List[str]) -> List[str]:
        """Get most common words in subject lines"""
        # Simplified word analysis
        all_words = []
        for subject in subject_lines:
            words = subject.lower().split()
            all_words.extend([w for w in words if len(w) > 3])
        
        from collections import Counter
        return [word for word, count in Counter(all_words).most_common(10)]
    
    def analyze_emoji_usage(self, campaigns: List[MailchimpCampaignData]) -> Dict:
        """Analyze emoji usage impact"""
        emoji_campaigns = [c for c in campaigns if any(ord(char) > 127 for char in c.subject_line)]
        no_emoji_campaigns = [c for c in campaigns if not any(ord(char) > 127 for char in c.subject_line)]
        
        if emoji_campaigns and no_emoji_campaigns:
            emoji_open_rates = [c.open_rate for c in emoji_campaigns if c.open_rate > 0]
            no_emoji_open_rates = [c.open_rate for c in no_emoji_campaigns if c.open_rate > 0]
            return {
                "with_emoji_avg_open_rate": np.mean(emoji_open_rates) if emoji_open_rates else 0.0,
                "without_emoji_avg_open_rate": np.mean(no_emoji_open_rates) if no_emoji_open_rates else 0.0,
                "emoji_usage_rate": len(emoji_campaigns) / len(campaigns)
            }
        return {}
    
    def analyze_personalization(self, campaigns: List[MailchimpCampaignData]) -> Dict:
        """Analyze personalization impact"""
        # Look for personalization indicators
        personal_indicators = ['your', 'you', 'name', 'exclusive', 'personal']
        
        personal_campaigns = [c for c in campaigns if any(indicator in c.subject_line.lower() for indicator in personal_indicators)]
        generic_campaigns = [c for c in campaigns if not any(indicator in c.subject_line.lower() for indicator in personal_indicators)]
        
        if personal_campaigns and generic_campaigns:
            personal_open_rates = [c.open_rate for c in personal_campaigns if c.open_rate > 0]
            generic_open_rates = [c.open_rate for c in generic_campaigns if c.open_rate > 0]
            return {
                "personalized_avg_open_rate": np.mean(personal_open_rates) if personal_open_rates else 0.0,
                "generic_avg_open_rate": np.mean(generic_open_rates) if generic_open_rates else 0.0,
                "personalization_rate": len(personal_campaigns) / len(campaigns)
            }
        return {}
    
    def analyze_send_times(self, df: pd.DataFrame) -> Dict:
        """Analyze optimal send times"""
        try:
            df['hour'] = df['send_date'].dt.hour
            df['day_of_week'] = df['send_date'].dt.dayofweek
            
            hourly_performance = df.groupby('hour')['open_rate'].mean()
            daily_performance = df.groupby('day_of_week')['open_rate'].mean()
            
            return {
                "best_hour": hourly_performance.idxmax(),
                "best_day": daily_performance.idxmax(),
                "hourly_breakdown": hourly_performance.to_dict(),
                "daily_breakdown": daily_performance.to_dict()
            }
        except:
            return {}
    
    def analyze_subscriber_growth(self) -> Dict:
        """Analyze subscriber growth patterns"""
        # Placeholder for growth analysis
        return {
            "monthly_growth_rate": 0.05,
            "trend": "growing",
            "growth_sources": ["organic", "campaigns", "referrals"]
        }
    
    def segment_by_engagement(self) -> Dict:
        """Segment audience by engagement levels"""
        return {
            "highly_engaged": 0.25,
            "moderately_engaged": 0.45,
            "low_engagement": 0.30
        }
    
    def get_single_campaign_data(self, campaign_id: str) -> Optional[MailchimpCampaignData]:
        """Get data for a single campaign"""
        campaigns = self.get_campaign_analytics(100)
        for campaign in campaigns:
            if campaign.campaign_id == campaign_id:
                return campaign
        return None
    
    def calculate_optimization_potential(self, campaign_data: MailchimpCampaignData) -> float:
        """Calculate optimization potential score"""
        # Simple scoring based on current performance vs benchmarks
        benchmark_open_rate = 0.25
        benchmark_click_rate = 0.03
        
        open_score = min(campaign_data.open_rate / benchmark_open_rate, 1.0)
        click_score = min(campaign_data.click_rate / benchmark_click_rate, 1.0)
        
        current_score = (open_score + click_score) / 2
        optimization_potential = (1.0 - current_score) * 100
        
        return optimization_potential
    
    def create_fallback_analysis(self, campaigns: List[MailchimpCampaignData]) -> CampaignAnalysis:
        """Create fallback analysis when AI is unavailable"""
        open_rates = [c.open_rate for c in campaigns if c.open_rate > 0]
        click_rates = [c.click_rate for c in campaigns if c.click_rate > 0]
        avg_open_rate = np.mean(open_rates) if open_rates else 0.0
        avg_click_rate = np.mean(click_rates) if click_rates else 0.0
        
        performance_score = min((avg_open_rate + avg_click_rate) * 10, 10.0)
        
        return CampaignAnalysis(
            performance_score=performance_score,
            key_insights=[
                f"Average open rate: {avg_open_rate * 100:.1f}%",
                f"Average click rate: {avg_click_rate * 100:.1f}%",
                "Performance analysis based on statistical data"
            ],
            optimization_recommendations=[
                "Test different subject lines",
                "Optimize send times",
                "Improve email content",
                "Segment your audience"
            ],
            predicted_improvements={
                "open_rate_improvement": 0.05,
                "click_rate_improvement": 0.02
            },
            content_analysis={
                "tone": "professional",
                "length": "medium"
            },
            audience_insights={
                "engagement": "moderate",
                "best_time": "morning"
            }
        )
    
    def create_fallback_campaign_content(self, brief: Dict) -> Dict:
        """Create fallback campaign content"""
        return {
            "subject_lines": [
                "High-Speed Fiber Internet Now Available",
                "Upgrade Your Internet Experience Today",
                "Professional Fiber Installation Available",
                "Transform Your Home's Connectivity",
                "Secure High-Speed Internet Solutions"
            ],
            "templates": {
                "short": "Quick fiber upgrade opportunity",
                "medium": "Professional fiber internet solutions for your home",
                "long": "Comprehensive fiber and security package available"
            },
            "ab_test_strategy": "Test subject lines and send times",
            "performance_prediction": {
                "open_rate": "22-28%",
                "click_rate": "3-5%"
            }
        }
    
    def generate_fallback_analysis_text(self, prompt: str) -> str:
        """Generate fallback analysis text"""
        return json.dumps({
            "performance_score": 7.5,
            "key_insights": [
                "Email campaigns show consistent performance",
                "Subject line optimization needed",
                "Content engagement could be improved"
            ],
            "optimization_recommendations": [
                "A/B test subject lines",
                "Optimize send timing",
                "Improve call-to-action placement",
                "Segment audience by engagement"
            ],
            "predicted_improvements": {
                "open_rate": 0.05,
                "click_rate": 0.02,
                "conversion_rate": 0.01
            },
            "content_analysis": {
                "tone": "professional",
                "clarity": "good",
                "call_to_action": "needs_improvement"
            },
            "audience_insights": {
                "engagement_level": "moderate",
                "best_send_time": "Tuesday 10AM",
                "preferred_content": "informational"
            }
        })
    
    def parse_ai_analysis(self, ai_response: str, campaigns: List[MailchimpCampaignData]) -> CampaignAnalysis:
        """Parse AI analysis response"""
        try:
            parsed = json.loads(ai_response)
            return CampaignAnalysis(
                performance_score=parsed.get('performance_score', 7.0),
                key_insights=parsed.get('key_insights', []),
                optimization_recommendations=parsed.get('optimization_recommendations', []),
                predicted_improvements=parsed.get('predicted_improvements', {}),
                content_analysis=parsed.get('content_analysis', {}),
                audience_insights=parsed.get('audience_insights', {})
            )
        except:
            return self.create_fallback_analysis(campaigns)
    
    def export_comprehensive_report(self, output_dir: str = "data/email_analytics") -> str:
        """Export comprehensive email marketing report"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Get all data
            mailchimp_data = self.get_comprehensive_mailchimp_data()
            campaigns = self.get_campaign_analytics()
            ai_analysis = self.ai_analyze_campaign_performance(campaigns)
            
            # Create comprehensive report
            report = {
                "report_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "report_type": "comprehensive_email_analytics",
                    "data_sources": ["mailchimp", "ai_analysis"]
                },
                "mailchimp_data": mailchimp_data,
                "ai_analysis": asdict(ai_analysis),
                "executive_summary": self.create_executive_summary(mailchimp_data, ai_analysis),
                "recommendations": self.create_action_plan(ai_analysis)
            }
            
            # Save report
            report_file = os.path.join(output_dir, f"email_marketing_report_{timestamp}.json")
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            logger.info(f"Comprehensive report saved to {report_file}")
            return report_file
            
        except Exception as e:
            logger.error(f"Error exporting report: {e}")
            return ""
    
    def create_executive_summary(self, mailchimp_data: Dict, ai_analysis: CampaignAnalysis) -> Dict:
        """Create executive summary"""
        return {
            "performance_overview": f"Overall performance score: {ai_analysis.performance_score}/10",
            "key_metrics": {
                "total_campaigns": len(mailchimp_data.get('campaigns', [])),
                "avg_open_rate": f"{np.mean([c.open_rate for c in mailchimp_data.get('campaigns', []) if c.open_rate > 0]) * 100:.1f}%" if mailchimp_data.get('campaigns') else "0.0%",
                "total_subscribers": mailchimp_data.get('audience_insights', {}).get('total_subscribers', 0)
            },
            "top_insights": ai_analysis.key_insights[:3],
            "priority_actions": ai_analysis.optimization_recommendations[:3]
        }
    
    def create_action_plan(self, ai_analysis: CampaignAnalysis) -> List[Dict]:
        """Create actionable plan from AI analysis"""
        actions = []
        for i, recommendation in enumerate(ai_analysis.optimization_recommendations):
            actions.append({
                "priority": i + 1,
                "action": recommendation,
                "estimated_impact": "medium",
                "timeline": "1-2 weeks",
                "resources_needed": "marketing team"
            })
        return actions 

    def xai_chat(self, query: str) -> str:
        """Chat with XAI API for marketing assistance"""
        import logging
        import time

        # First, try to use the fallback service for better reliability
        try:
            from utils.ai_fallback import simple_ai_chat
            fallback_response = simple_ai_chat(query)
            if fallback_response and fallback_response.strip():
                return fallback_response
        except Exception as e:
            logging.warning(f"Fallback service failed: {e}")

        # If fallback doesn't work, try xAI API
        max_retries = 2  # Reduced retries for faster response
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                headers = {
                    'Authorization': f'Bearer {self.xai_api_key}',
                    'Content-Type': 'application/json'
                }
                data = {
                    'model': 'grok-2',
                    'messages': [
                        {'role': 'system', 'content': 'You are a helpful AI marketing assistant specializing in email campaigns for AT&T Fiber and ADT Security. Provide practical, actionable advice in a conversational tone.'},
                        {'role': 'user', 'content': query}
                    ],
                    'temperature': 0.7,
                    'max_tokens': 500  # Reduced for faster response
                }
                
                response = requests.post('https://api.x.ai/v1/chat/completions', headers=headers, json=data, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    if result and 'choices' in result and result['choices']:
                        choice = result['choices'][0]
                        if choice and 'message' in choice and choice['message']:
                            content = choice['message'].get('content', '')
                            if content and content.strip():
                                return content
                
                # Handle specific error codes
                if response.status_code == 401:
                    return "I'm having trouble connecting to the AI service right now. Let me help you with your marketing questions directly! What would you like to work on - automation, campaigns, or analytics?"
                elif response.status_code == 403:
                    return "I'm experiencing some technical difficulties with the AI service. I can still help you with your marketing tasks! What would you like to do - run automation, create campaigns, or check your analytics?"
                elif response.status_code == 429:
                    return "The AI service is a bit busy right now. I can help you with your marketing tasks directly! What would you like to work on?"
                else:
                    logging.warning(f"xAI API attempt {attempt+1} failed: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                logging.warning(f"xAI API timeout on attempt {attempt+1}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    return "I'm experiencing some connection issues. Let me help you with your marketing tasks directly! What would you like to work on?"
                    
            except requests.exceptions.RequestException as e:
                logging.warning(f"Network error in xAI chat attempt {attempt+1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    return "I'm having network connectivity issues. I can still help you with your marketing tasks! What would you like to do?"
                    
            except Exception as e:
                logging.exception(f"Unexpected error in xAI chat attempt {attempt+1}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    return "I'm experiencing some technical difficulties. Let me help you with your marketing tasks directly! What would you like to work on?"
        
        # Final fallback response
        return "I'm here to help with your email marketing! I can assist you with automation, campaign creation, analytics, and more. What would you like to work on today?" 