"""
API Cost Tracker - Monitor and track costs for all APIs used in AT&T Fiber Tracker
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class APICostTracker:
    """Track API usage and costs across all services"""
    
    # API Pricing (as of 2024 - prices may change)
    API_PRICING = {
        'google_vision': {
            'name': 'Google Vision API',
            'free_tier': 1000,  # requests per month
            'cost_per_request': 0.0015,  # $1.50 per 1000 requests
            'billing_unit': 'request'
        },
        'google_maps': {
            'name': 'Google Maps Geocoding API',
            'free_tier': 40000,  # requests per month ($200 credit)
            'cost_per_request': 0.005,  # $5.00 per 1000 requests
            'billing_unit': 'request'
        },
        'batchdata': {
            'name': 'BatchData API',
            'free_tier': 0,  # No free tier
            'cost_per_request': 0.10,  # $0.10 per lookup
            'billing_unit': 'lookup'
        },
        'mailchimp': {
            'name': 'Mailchimp API',
            'free_tier': 2000,  # contacts for free plan
            'cost_per_contact': 0.00,  # Varies by plan
            'billing_unit': 'contact',
            'note': 'Cost varies by plan - Free: 2k contacts, Essentials: $10/month'
        },
        'activeknocker': {
            'name': 'ActiveKnocker API',
            'free_tier': 0,
            'cost_per_request': 0.05,  # Estimated
            'billing_unit': 'upload'
        },
        'openai': {
            'name': 'OpenAI API',
            'free_tier': 0,
            'cost_per_token': 0.0000015,  # GPT-3.5-turbo input
            'billing_unit': 'token'
        },
        'xai': {
            'name': 'XAI API',
            'free_tier': 0,
            'cost_per_token': 0.000001,  # Estimated
            'billing_unit': 'token'
        }
    }
    
    def __init__(self, tracking_file='data/api_costs.json'):
        self.tracking_file = tracking_file
        self.ensure_tracking_file()
        
    def ensure_tracking_file(self):
        """Ensure the tracking file exists"""
        os.makedirs(os.path.dirname(self.tracking_file), exist_ok=True)
        
        if not os.path.exists(self.tracking_file):
            initial_data = {
                'created': datetime.now().isoformat(),
                'monthly_usage': {},
                'daily_usage': {},
                'total_costs': {},
                'last_reset': datetime.now().replace(day=1).isoformat()
            }
            self.save_data(initial_data)
    
    def load_data(self) -> Dict:
        """Load tracking data from file"""
        try:
            with open(self.tracking_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading cost tracking data: {e}")
            return {}
    
    def save_data(self, data: Dict):
        """Save tracking data to file"""
        try:
            with open(self.tracking_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving cost tracking data: {e}")
    
    def track_api_usage(self, api_name: str, count: int = 1, additional_data: Dict = None):
        """Track API usage"""
        data = self.load_data()
        today = datetime.now().strftime('%Y-%m-%d')
        current_month = datetime.now().strftime('%Y-%m')
        
        # Initialize structures if needed
        if 'monthly_usage' not in data:
            data['monthly_usage'] = {}
        if 'daily_usage' not in data:
            data['daily_usage'] = {}
        if current_month not in data['monthly_usage']:
            data['monthly_usage'][current_month] = {}
        if today not in data['daily_usage']:
            data['daily_usage'][today] = {}
        
        # Track monthly usage
        if api_name not in data['monthly_usage'][current_month]:
            data['monthly_usage'][current_month][api_name] = 0
        data['monthly_usage'][current_month][api_name] += count
        
        # Track daily usage
        if api_name not in data['daily_usage'][today]:
            data['daily_usage'][today][api_name] = 0
        data['daily_usage'][today][api_name] += count
        
        # Add additional data if provided
        if additional_data:
            if 'details' not in data:
                data['details'] = {}
            if today not in data['details']:
                data['details'][today] = []
            
            data['details'][today].append({
                'timestamp': datetime.now().isoformat(),
                'api': api_name,
                'count': count,
                **additional_data
            })
        
        self.save_data(data)
        logger.info(f"Tracked {count} {api_name} API calls")
    
    def calculate_costs(self) -> Dict:
        """Calculate current costs for all APIs"""
        data = self.load_data()
        current_month = datetime.now().strftime('%Y-%m')
        
        if current_month not in data.get('monthly_usage', {}):
            return {}
        
        monthly_usage = data['monthly_usage'][current_month]
        costs = {}
        total_cost = 0
        
        for api_name, usage_count in monthly_usage.items():
            if api_name in self.API_PRICING:
                pricing = self.API_PRICING[api_name]
                
                # Calculate cost based on free tier
                if usage_count <= pricing['free_tier']:
                    cost = 0
                    free_remaining = pricing['free_tier'] - usage_count
                    paid_usage = 0
                else:
                    paid_usage = usage_count - pricing['free_tier']
                    free_remaining = 0
                    
                    if 'cost_per_request' in pricing:
                        cost = paid_usage * pricing['cost_per_request']
                    elif 'cost_per_contact' in pricing:
                        cost = paid_usage * pricing['cost_per_contact']
                    elif 'cost_per_token' in pricing:
                        cost = paid_usage * pricing['cost_per_token']
                    else:
                        cost = 0
                
                costs[api_name] = {
                    'name': pricing['name'],
                    'usage': usage_count,
                    'free_tier': pricing['free_tier'],
                    'free_remaining': free_remaining,
                    'paid_usage': paid_usage,
                    'cost': cost,
                    'billing_unit': pricing['billing_unit']
                }
                
                total_cost += cost
        
        return {
            'costs': costs,
            'total_monthly_cost': total_cost,
            'month': current_month
        }
    
    def get_usage_summary(self, days: int = 30) -> Dict:
        """Get usage summary for the last N days"""
        data = self.load_data()
        cutoff_date = datetime.now() - timedelta(days=days)
        
        summary = {}
        total_requests = 0
        
        for date_str, daily_usage in data.get('daily_usage', {}).items():
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d')
                if date >= cutoff_date:
                    for api_name, count in daily_usage.items():
                        if api_name not in summary:
                            summary[api_name] = 0
                        summary[api_name] += count
                        total_requests += count
            except ValueError:
                continue
        
        return {
            'period_days': days,
            'api_usage': summary,
            'total_requests': total_requests
        }
    
    def get_cost_projection(self) -> Dict:
        """Project monthly costs based on current usage"""
        current_month = datetime.now().strftime('%Y-%m')
        days_in_month = datetime.now().replace(month=datetime.now().month + 1, day=1) - timedelta(days=1)
        days_elapsed = datetime.now().day
        days_remaining = days_in_month.day - days_elapsed
        
        current_costs = self.calculate_costs()
        
        if not current_costs or days_elapsed == 0:
            return {}
        
        projections = {}
        
        for api_name, cost_data in current_costs['costs'].items():
            daily_average = cost_data['usage'] / days_elapsed
            projected_monthly_usage = daily_average * days_in_month.day
            
            pricing = self.API_PRICING.get(api_name, {})
            
            # Calculate projected cost
            if projected_monthly_usage <= pricing.get('free_tier', 0):
                projected_cost = 0
            else:
                paid_usage = projected_monthly_usage - pricing.get('free_tier', 0)
                cost_per_unit = pricing.get('cost_per_request', pricing.get('cost_per_contact', pricing.get('cost_per_token', 0)))
                projected_cost = paid_usage * cost_per_unit
            
            projections[api_name] = {
                'current_usage': cost_data['usage'],
                'daily_average': daily_average,
                'projected_monthly_usage': projected_monthly_usage,
                'projected_cost': projected_cost
            }
        
        total_projected = sum(p['projected_cost'] for p in projections.values())
        
        return {
            'projections': projections,
            'total_projected_monthly_cost': total_projected,
            'days_elapsed': days_elapsed,
            'days_remaining': days_remaining
        }
    
    def reset_monthly_data(self):
        """Reset monthly data (called at beginning of new month)"""
        data = self.load_data()
        current_month = datetime.now().strftime('%Y-%m')
        
        # Archive previous month if it exists
        if 'monthly_usage' in data:
            if 'archived_months' not in data:
                data['archived_months'] = {}
            
            for month, usage in data['monthly_usage'].items():
                if month != current_month:
                    data['archived_months'][month] = usage
            
            # Keep only current month
            data['monthly_usage'] = {current_month: data['monthly_usage'].get(current_month, {})}
        
        data['last_reset'] = datetime.now().isoformat()
        self.save_data(data)
    
    def export_cost_report(self, output_file: str = None) -> str:
        """Export a detailed cost report"""
        if not output_file:
            output_file = f"api_cost_report_{datetime.now().strftime('%Y%m%d')}.json"
        
        costs = self.calculate_costs()
        usage_summary = self.get_usage_summary()
        projections = self.get_cost_projection()
        
        report = {
            'generated': datetime.now().isoformat(),
            'current_costs': costs,
            'usage_summary': usage_summary,
            'cost_projections': projections,
            'api_pricing': self.API_PRICING
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return output_file

# Global tracker instance
cost_tracker = APICostTracker()

# Convenience functions for easy tracking
def track_google_vision_usage(count: int = 1, operation: str = "text_detection"):
    """Track Google Vision API usage"""
    cost_tracker.track_api_usage('google_vision', count, {'operation': operation})

def track_google_maps_usage(count: int = 1, operation: str = "geocoding"):
    """Track Google Maps API usage"""
    cost_tracker.track_api_usage('google_maps', count, {'operation': operation})

def track_batchdata_usage(count: int = 1, operation: str = "contact_lookup"):
    """Track BatchData API usage"""
    cost_tracker.track_api_usage('batchdata', count, {'operation': operation})

def track_mailchimp_usage(count: int = 1, operation: str = "contact_upload"):
    """Track Mailchimp API usage"""
    cost_tracker.track_api_usage('mailchimp', count, {'operation': operation})

def track_activeknocker_usage(count: int = 1, operation: str = "upload"):
    """Track ActiveKnocker API usage"""
    cost_tracker.track_api_usage('activeknocker', count, {'operation': operation})

def get_current_costs():
    """Get current API costs"""
    return cost_tracker.calculate_costs()

def get_cost_summary():
    """Get a formatted cost summary"""
    costs = cost_tracker.calculate_costs()
    projections = cost_tracker.get_cost_projection()
    
    if not costs:
        return "No API usage tracked this month."
    
    summary = []
    summary.append(f"API Cost Summary for {costs['month']}")
    summary.append("=" * 50)
    
    for api_name, data in costs['costs'].items():
        summary.append(f"\n{data['name']}:")
        summary.append(f"  Usage: {data['usage']} {data['billing_unit']}s")
        summary.append(f"  Free Tier: {data['free_tier']} ({data['free_remaining']} remaining)")
        summary.append(f"  Paid Usage: {data['paid_usage']}")
        summary.append(f"  Cost: ${data['cost']:.2f}")
    
    summary.append(f"\nTotal Monthly Cost: ${costs['total_monthly_cost']:.2f}")
    
    if projections:
        summary.append(f"Projected Monthly Cost: ${projections['total_projected_monthly_cost']:.2f}")
    
    return "\n".join(summary) 