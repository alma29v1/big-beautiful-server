"""Service for XAI Email Assistant functionality."""

import openai
from typing import Dict, List, Optional
import logging
from ..config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

class XAIService:
    """Service for AI-powered email campaign generation."""
    
    def __init__(self):
        """Initialize the XAI service."""
        openai.api_key = OPENAI_API_KEY
        
    def generate_campaign(self, campaign_data: Dict) -> Dict:
        """Generate an email campaign using AI.
        
        Args:
            campaign_data: Dictionary containing campaign information
                - target_audience: Description of the target audience
                - key_points: List of key points to include
                - tone: Desired tone (professional, friendly, etc.)
                - call_to_action: What action you want recipients to take
                
        Returns:
            Dict containing the generated campaign content
        """
        try:
            # Construct the prompt
            prompt = f"""Create a compelling email campaign for AT&T Fiber availability:

Target Audience: {campaign_data.get('target_audience')}
Key Points to Include:
{chr(10).join('- ' + point for point in campaign_data.get('key_points', []))}
Tone: {campaign_data.get('tone', 'Professional')}
Call to Action: {campaign_data.get('call_to_action')}

Generate:
1. Subject line
2. Email body
3. Call-to-action button text"""

            # Generate content using OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert email marketing copywriter specializing in fiber internet services."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            # Parse the response
            content = response.choices[0].message.content
            
            # Split into components (basic parsing, can be improved)
            parts = content.split('\n\n')
            subject_line = next((p.replace('Subject line:', '').strip() 
                               for p in parts if 'Subject line:' in p), '')
            
            email_body = next((p.replace('Email body:', '').strip() 
                             for p in parts if 'Email body:' in p), '')
            
            cta_text = next((p.replace('Call-to-action:', '').strip() 
                           for p in parts if 'Call-to-action:' in p), '')
            
            return {
                "success": True,
                "campaign": {
                    "subject_line": subject_line,
                    "email_body": email_body,
                    "cta_text": cta_text
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating campaign: {str(e)}")
            return {"error": str(e)}
    
    def review_campaign(self, campaign_content: str) -> Dict:
        """Review and optimize an existing campaign.
        
        Args:
            campaign_content: The existing campaign content to review
            
        Returns:
            Dict containing review feedback and suggestions
        """
        try:
            prompt = f"""Review this email campaign and provide specific suggestions for improvement:

{campaign_content}

Analyze and provide feedback on:
1. Subject line effectiveness
2. Opening hook
3. Value proposition clarity
4. Persuasiveness
5. Call-to-action strength
6. Tone and style
7. Specific improvement suggestions"""

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert email marketing analyst specializing in fiber internet services."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            return {
                "success": True,
                "feedback": response.choices[0].message.content
            }
            
        except Exception as e:
            logger.error(f"Error reviewing campaign: {str(e)}")
            return {"error": str(e)}
    
    def optimize_campaign(self, campaign_content: str, feedback: str) -> Dict:
        """Optimize a campaign based on feedback.
        
        Args:
            campaign_content: The original campaign content
            feedback: Previous review feedback
            
        Returns:
            Dict containing the optimized campaign
        """
        try:
            prompt = f"""Optimize this email campaign based on the feedback provided:

Original Campaign:
{campaign_content}

Feedback:
{feedback}

Please provide an optimized version that addresses all feedback points while maintaining the core message."""

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert email marketing copywriter specializing in fiber internet services."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            
            return {
                "success": True,
                "optimized_content": response.choices[0].message.content
            }
            
        except Exception as e:
            logger.error(f"Error optimizing campaign: {str(e)}")
            return {"error": str(e)} 