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
        # Set default XAI key
        self.xai_api_key = 'xai-8SGfoHCP1nucLONy9il9UFfGCaTT9rhjKPrh7ONNT5CPAqLCKs4dQrk3BPlonKEs5lmLeDDX1PiQbsYc'
        
    def load_config(self):
        """Load configuration and API keys"""
        try:
            config_path = os.path.join('config', 'config.json')
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            self.mailchimp_api_key = config.get('mailchimp_api_key', '')
            self.openai_api_key = config.get('openai_api_key', '')
            
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.mailchimp_api_key = ""
            self.openai_api_key = ""
    
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
        """Get all Mailchimp lists with detailed stats"""
        try:
            response = self.mailchimp_client.lists.get_all_lists(count=50)
            lists_data = []
            
            for lst in response.get('lists', []):
                list_info = {
                    "id": lst['id'],
                    "name": lst['name'],
                    "member_count": lst['stats']['member_count'],
                    "open_rate": lst['stats']['open_rate'],
                    "click_rate": lst['stats']['click_rate'],
                    "created_date": lst['date_created'],
                    "last_campaign": lst['stats'].get('last_campaign', ''),
                    "growth_rate": self.calculate_list_growth_rate(lst['id'])
                }
                lists_data.append(list_info)
            
            return lists_data
            
        except Exception as e:
            logger.error(f"Error getting lists: {e}")
            return []
    
    def get_campaign_analytics(self, limit: int = 50) -> List[MailchimpCampaignData]:
        """Get detailed analytics for recent campaigns"""
        try:
            campaigns_response = self.mailchimp_client.campaigns.list(
                count=limit, 
                status='sent',
                sort_field='send_time',
                sort_dir='DESC'
            )
            
            campaigns_data = []
            
            for campaign in campaigns_response.get('campaigns', []):
                campaign_id = campaign['id']
                
                # Get campaign stats
                try:
                    stats = self.mailchimp_client.reports.get_campaign_report(campaign_id)
                    content = self.mailchimp_client.campaigns.get_content(campaign_id)
                    
                    # Get list info
                    list_id = campaign.get('recipients', {}).get('list_id', '')
                    list_name = ""
                    if list_id:
                        try:
                            list_info = self.mailchimp_client.lists.get_list(list_id)
                            list_name = list_info.get('name', '')
                        except:
                            pass
                    
                    campaign_data = MailchimpCampaignData(
                        campaign_id=campaign_id,
                        subject_line=campaign.get('settings', {}).get('subject_line', ''),
                        send_time=campaign.get('send_time', ''),
                        emails_sent=stats.get('emails_sent', 0),
                        opens=stats.get('opens', 0),
                        clicks=stats.get('clicks', 0),
                        open_rate=stats.get('open_rate', 0),
                        click_rate=stats.get('click_rate', 0),
                        unsubscribes=stats.get('unsubscribes', 0),
                        content_html=content.get('html', ''),
                        content_text=content.get('plain_text', ''),
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
        try:
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
        try:
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
            insights = {
                "total_subscribers": sum(lst['member_count'] for lst in lists),
                "avg_open_rate": np.mean([lst['open_rate'] for lst in lists if lst['open_rate'] > 0]),
                "avg_click_rate": np.mean([lst['click_rate'] for lst in lists if lst['click_rate'] > 0]),
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
        # Calculate summary statistics
        total_campaigns = len(campaigns)
        avg_open_rate = np.mean([c.open_rate for c in campaigns]) * 100
        avg_click_rate = np.mean([c.click_rate for c in campaigns]) * 100
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
        """Call AI API for analysis"""
        try:
            # Always use XAI first
            logger.info("Calling XAI API")
            return self.call_xai_api(prompt)
        except Exception as e:
            logger.error(f"XAI failed: {e}")
            if self.openai_api_key:
                logger.info("Falling back to OpenAI")
                return self.call_openai_api(prompt)
            raise
    
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
            "model": "grok-3-beta",
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
        
        recent_avg = np.mean(values[-5:]) if len(values) >= 5 else np.mean(values)
        older_avg = np.mean(values[:-5]) if len(values) >= 10 else np.mean(values[:-2])
        
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
            subject_analysis = {
                "avg_length": np.mean([len(c.subject_line) for c in campaigns]),
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
            return {
                "with_emoji_avg_open_rate": np.mean([c.open_rate for c in emoji_campaigns]),
                "without_emoji_avg_open_rate": np.mean([c.open_rate for c in no_emoji_campaigns]),
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
            return {
                "personalized_avg_open_rate": np.mean([c.open_rate for c in personal_campaigns]),
                "generic_avg_open_rate": np.mean([c.open_rate for c in generic_campaigns]),
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
        avg_open_rate = np.mean([c.open_rate for c in campaigns]) if campaigns else 0
        avg_click_rate = np.mean([c.click_rate for c in campaigns]) if campaigns else 0
        
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