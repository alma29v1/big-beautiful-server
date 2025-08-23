#!/usr/bin/env python3
"""
AI Image Optimization Service
Advanced image A/B testing, rotation, and performance analysis for email campaigns
"""

import os
import json
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import sqlite3
from dataclasses import dataclass
from enum import Enum

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ImagePerformanceData:
    """Data class for tracking image performance metrics"""
    image_url: str
    campaign_type: str
    total_sends: int = 0
    total_opens: int = 0
    total_clicks: int = 0
    open_rate: float = 0.0
    click_rate: float = 0.0
    conversion_rate: float = 0.0
    engagement_score: float = 0.0
    last_used: Optional[str] = None
    performance_trend: str = "neutral"  # improving, declining, stable, neutral

@dataclass 
class ImageTestResult:
    """Results from A/B testing different images"""
    winning_image: str
    confidence_level: float
    open_rate_lift: float
    click_rate_lift: float
    statistical_significance: bool
    sample_size: int

class ImageCategory(Enum):
    """Image categories for different campaign types"""
    FIBER_TECH = "fiber_technology"
    FIBER_HOME = "fiber_home_office"  
    FIBER_SPEED = "fiber_speed_performance"
    ADT_SECURITY = "adt_security"
    ADT_HOME = "adt_home_protection"
    INCIDENT_EMERGENCY = "incident_emergency"
    GENERAL_HOME = "general_home"
    COMPANY_BRANDING = "company_branding"

class AIImageOptimizationService:
    """AI-powered image optimization and A/B testing service"""
    
    def __init__(self):
        self.db_path = "image_performance.db"
        self.performance_data = {}
        self.rotation_settings = {}
        self._init_database()
        self._load_performance_data()
        self._setup_rotation_defaults()
    
    def _init_database(self):
        """Initialize SQLite database for image performance tracking"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create image performance table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS image_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    image_url TEXT NOT NULL,
                    campaign_type TEXT NOT NULL,
                    campaign_id TEXT,
                    timestamp TEXT,
                    emails_sent INTEGER DEFAULT 0,
                    opens INTEGER DEFAULT 0,
                    clicks INTEGER DEFAULT 0,
                    conversions INTEGER DEFAULT 0,
                    open_rate REAL DEFAULT 0.0,
                    click_rate REAL DEFAULT 0.0,
                    conversion_rate REAL DEFAULT 0.0,
                    engagement_score REAL DEFAULT 0.0,
                    UNIQUE(image_url, campaign_type)
                )
            ''')
            
            # Create A/B test results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ab_test_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    test_id TEXT UNIQUE,
                    campaign_type TEXT,
                    image_a TEXT,
                    image_b TEXT,
                    winner TEXT,
                    confidence_level REAL,
                    open_rate_lift REAL,
                    click_rate_lift REAL,
                    statistical_significance BOOLEAN,
                    sample_size INTEGER,
                    test_duration_days INTEGER,
                    created_at TEXT,
                    completed_at TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("✅ Image performance database initialized")
            
        except Exception as e:
            logger.error(f"❌ Database initialization error: {e}")
    
    def _setup_rotation_defaults(self):
        """Set up default rotation settings for different campaign types"""
        self.rotation_settings = {
            'att_fiber': {
                'rotation_enabled': True,
                'rotation_frequency': 'weekly',  # daily, weekly, monthly
                'min_sample_size': 50,  # Minimum sends before rotation
                'performance_threshold': 0.05,  # 5% improvement needed to switch
                'auto_optimize': True
            },
            'adt_security': {
                'rotation_enabled': True, 
                'rotation_frequency': 'weekly',
                'min_sample_size': 30,
                'performance_threshold': 0.05,
                'auto_optimize': True
            },
            'incident_alert': {
                'rotation_enabled': False,  # Emergency campaigns use proven images
                'rotation_frequency': 'monthly',
                'min_sample_size': 20,
                'performance_threshold': 0.03,
                'auto_optimize': False
            }
        }
    
    def get_optimal_image(self, campaign_type: str, audience_size: int = 0) -> Tuple[str, Dict]:
        """
        Get the optimal image for a campaign based on AI analysis and performance data
        
        Args:
            campaign_type: Type of campaign (att_fiber, adt_security, etc.)
            audience_size: Size of target audience for this campaign
            
        Returns:
            Tuple of (image_url, optimization_data)
        """
        try:
            # Get available images for campaign type
            available_images = self._get_available_images(campaign_type)
            
            if not available_images:
                logger.warning(f"No images available for campaign type: {campaign_type}")
                return self._get_fallback_image(campaign_type), {"strategy": "fallback"}
            
            # Get performance data for all images
            image_performance = {}
            for img_url in available_images:
                performance = self._get_image_performance(img_url, campaign_type)
                image_performance[img_url] = performance
            
            # AI-driven image selection strategy
            strategy_data = self._analyze_optimal_selection_strategy(
                image_performance, 
                campaign_type, 
                audience_size
            )
            
            selected_image = self._select_image_by_strategy(
                image_performance, 
                strategy_data
            )
            
            # Log selection for tracking
            self._log_image_selection(selected_image, campaign_type, strategy_data)
            
            return selected_image, strategy_data
            
        except Exception as e:
            logger.error(f"Error getting optimal image: {e}")
            return self._get_fallback_image(campaign_type), {"strategy": "error_fallback"}
    
    def _analyze_optimal_selection_strategy(self, performance_data: Dict, campaign_type: str, audience_size: int) -> Dict:
        """Use AI analysis to determine the best image selection strategy"""
        
        # Calculate performance metrics
        total_images = len(performance_data)
        tested_images = len([p for p in performance_data.values() if p.total_sends > 0])
        
        # Identify performance leaders
        if tested_images > 0:
            sorted_by_performance = sorted(
                performance_data.items(),
                key=lambda x: x[1].engagement_score,
                reverse=True
            )
            
            best_performer = sorted_by_performance[0]
            best_engagement = best_performer[1].engagement_score
            
            # Strategy decisions based on data
            if tested_images < total_images * 0.5:
                # Not enough images tested - exploration phase
                strategy = "explore"
                reason = f"Only {tested_images}/{total_images} images tested. Exploring untested options."
                
            elif best_engagement > 0.15 and best_performer[1].total_sends > 100:
                # Clear winner with statistical significance
                strategy = "exploit_winner" 
                reason = f"Strong performer found: {best_engagement:.1%} engagement with {best_performer[1].total_sends} sends"
                
            elif campaign_type == 'incident_alert':
                # Emergency campaigns prioritize proven, trustworthy images
                strategy = "proven_safe"
                reason = "Incident campaigns use proven, trustworthy imagery for credibility"
                
            elif audience_size > 500:
                # Large audience - use A/B testing
                strategy = "ab_test"
                reason = f"Large audience ({audience_size}) - perfect for A/B testing"
                
            else:
                # Regular rotation strategy
                strategy = "smart_rotation"
                reason = "Standard smart rotation based on performance trends"
        else:
            # No performance data - start with rotation
            strategy = "initial_rotation"
            reason = "No performance data available. Starting systematic testing."
        
        return {
            "strategy": strategy,
            "reason": reason,
            "performance_summary": {
                "total_images": total_images,
                "tested_images": tested_images,
                "best_engagement": best_engagement if tested_images > 0 else 0,
                "audience_size": audience_size
            }
        }
    
    def _select_image_by_strategy(self, performance_data: Dict, strategy_data: Dict) -> str:
        """Select image based on the determined strategy"""
        
        strategy = strategy_data["strategy"]
        images = list(performance_data.keys())
        
        if strategy == "exploit_winner":
            # Use the best performing image
            best_image = max(
                performance_data.items(),
                key=lambda x: x[1].engagement_score
            )[0]
            return best_image
            
        elif strategy == "explore":
            # Choose an untested or under-tested image
            untested = [img for img, perf in performance_data.items() if perf.total_sends == 0]
            if untested:
                return random.choice(untested)
            else:
                # Choose least tested
                least_tested = min(
                    performance_data.items(),
                    key=lambda x: x[1].total_sends
                )[0]
                return least_tested
                
        elif strategy == "ab_test":
            # Return top 2 performers for A/B testing
            sorted_performers = sorted(
                performance_data.items(),
                key=lambda x: x[1].engagement_score,
                reverse=True
            )
            
            # For now, return the top performer 
            # (A/B testing would be handled at the campaign level)
            return sorted_performers[0][0]
            
        elif strategy == "proven_safe":
            # For incident alerts, prioritize company logo or proven security imagery
            seaside_logo = "https://seasidesecurity.net/wp-content/uploads/2025/04/DLR.23.8.17-DealerComboLogo_SeasideSecurity_Horz_RGB_BlueGray-scaled-e1746532770501.webp"
            if seaside_logo in images:
                return seaside_logo
            else:
                # Choose image with highest total sends (most proven)
                most_used = max(
                    performance_data.items(),
                    key=lambda x: x[1].total_sends
                )[0]
                return most_used
                
        elif strategy == "smart_rotation":
            # Rotate based on performance trends and recency
            current_time = datetime.now()
            
            # Score images based on performance and recency
            scored_images = []
            for img_url, perf in performance_data.items():
                recency_score = 0
                if perf.last_used:
                    days_since_used = (current_time - datetime.fromisoformat(perf.last_used)).days
                    recency_score = min(days_since_used / 7, 1.0)  # Max score after 1 week
                else:
                    recency_score = 1.0  # Never used gets max recency score
                
                combined_score = (perf.engagement_score * 0.7) + (recency_score * 0.3)
                scored_images.append((img_url, combined_score))
            
            # Choose best combined score
            best_combined = max(scored_images, key=lambda x: x[1])
            return best_combined[0]
            
        else:  # initial_rotation or fallback
            # Random selection for initial testing
            return random.choice(images)
    
    def create_ab_test_campaign(self, campaign_type: str, audience_size: int) -> Dict:
        """Create an A/B test campaign with different images"""
        
        try:
            # Get top 2 image candidates for testing
            available_images = self._get_available_images(campaign_type)
            
            if len(available_images) < 2:
                return {"error": "Need at least 2 images for A/B testing"}
            
            # Select images for testing
            performance_data = {}
            for img_url in available_images:
                performance_data[img_url] = self._get_image_performance(img_url, campaign_type)
            
            # Choose 2 most promising candidates
            candidates = self._select_ab_test_candidates(performance_data)
            
            test_id = f"ab_test_{campaign_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            ab_test_config = {
                "test_id": test_id,
                "campaign_type": campaign_type,
                "image_a": candidates[0],
                "image_b": candidates[1],
                "split_percentage": 50,  # 50/50 split
                "min_sample_size": max(50, audience_size * 0.1),  # 10% of audience or min 50
                "test_duration_days": 7,
                "success_metrics": ["open_rate", "click_rate", "engagement_score"],
                "statistical_confidence_required": 0.95,
                "created_at": datetime.now().isoformat()
            }
            
            # Save A/B test configuration
            self._save_ab_test_config(ab_test_config)
            
            logger.info(f"✅ A/B test created: {test_id}")
            return ab_test_config
            
        except Exception as e:
            logger.error(f"Error creating A/B test: {e}")
            return {"error": str(e)}
    
    def analyze_campaign_image_performance(self, campaign_results: Dict) -> Dict:
        """
        Analyze the performance of images used in completed campaigns
        
        Args:
            campaign_results: Results from email campaign including metrics
            
        Returns:
            Analysis results and optimization recommendations
        """
        try:
            campaign_id = campaign_results.get('campaign_id')
            image_url = campaign_results.get('image_url')
            campaign_type = campaign_results.get('campaign_type')
            
            # Extract performance metrics
            emails_sent = campaign_results.get('emails_sent', 0)
            opens = campaign_results.get('opens', 0) 
            clicks = campaign_results.get('clicks', 0)
            conversions = campaign_results.get('conversions', 0)
            
            # Calculate rates
            open_rate = opens / emails_sent if emails_sent > 0 else 0
            click_rate = clicks / emails_sent if emails_sent > 0 else 0
            conversion_rate = conversions / emails_sent if emails_sent > 0 else 0
            
            # Calculate engagement score (weighted combination)
            engagement_score = (open_rate * 0.3) + (click_rate * 0.5) + (conversion_rate * 0.2)
            
            # Update performance database
            self._update_image_performance(
                image_url=image_url,
                campaign_type=campaign_type,
                campaign_id=campaign_id,
                emails_sent=emails_sent,
                opens=opens,
                clicks=clicks,
                conversions=conversions,
                open_rate=open_rate,
                click_rate=click_rate,
                conversion_rate=conversion_rate,
                engagement_score=engagement_score
            )
            
            # Generate AI insights and recommendations
            insights = self._generate_performance_insights(
                image_url, campaign_type, open_rate, click_rate, engagement_score
            )
            
            # Check if this triggers any optimization recommendations
            optimization_recommendations = self._generate_optimization_recommendations(
                campaign_type, performance_data
            )
            
            analysis_result = {
                "image_url": image_url,
                "campaign_type": campaign_type,
                "performance_metrics": {
                    "open_rate": open_rate,
                    "click_rate": click_rate,
                    "conversion_rate": conversion_rate,
                    "engagement_score": engagement_score
                },
                "insights": insights,
                "optimization_recommendations": optimization_recommendations,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"✅ Image performance analyzed for campaign {campaign_id}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing image performance: {e}")
            return {"error": str(e)}
    
    def get_image_rotation_recommendations(self, campaign_type: str) -> Dict:
        """Get AI recommendations for image rotation strategy"""
        
        try:
            # Get all performance data for this campaign type
            performance_data = self._get_all_campaign_type_performance(campaign_type)
            
            if not performance_data:
                return {
                    "recommendation": "start_systematic_testing",
                    "reason": "No performance data available. Start with systematic image testing.",
                    "suggested_images": self._get_available_images(campaign_type)[:3],
                    "testing_schedule": "weekly_rotation"
                }
            
            # Analyze current performance landscape
            analysis = self._analyze_performance_landscape(performance_data)
            
            # Generate specific recommendations
            if analysis["clear_winner"]:
                recommendation = {
                    "recommendation": "exploit_winner",
                    "reason": f"Clear winner identified with {analysis['winner_performance']:.1%} engagement",
                    "primary_image": analysis["best_image"],
                    "backup_images": analysis["secondary_performers"][:2],
                    "testing_schedule": "monthly_validation"
                }
            elif analysis["needs_more_data"]:
                recommendation = {
                    "recommendation": "accelerate_testing", 
                    "reason": "Insufficient data for optimization. Accelerate testing phase.",
                    "suggested_images": analysis["untested_images"],
                    "testing_schedule": "weekly_rotation"
                }
            else:
                recommendation = {
                    "recommendation": "smart_rotation",
                    "reason": "Continue data-driven rotation with performance tracking",
                    "rotation_candidates": analysis["top_performers"][:4],
                    "testing_schedule": "bi_weekly_rotation"
                }
            
            # Add performance context
            recommendation["performance_context"] = {
                "total_campaigns": len(performance_data),
                "avg_engagement": analysis["avg_engagement"],
                "performance_trend": analysis["trend"],
                "last_updated": datetime.now().isoformat()
            }
            
            return recommendation
            
        except Exception as e:
            logger.error(f"Error generating rotation recommendations: {e}")
            return {"error": str(e)}
    
    def generate_image_performance_report(self, campaign_type: str = None) -> Dict:
        """Generate a comprehensive image performance report"""
        
        try:
            if campaign_type:
                report = self._generate_single_campaign_report(campaign_type)
            else:
                report = self._generate_comprehensive_report()
            
            # Add AI insights
            report["ai_insights"] = self._generate_report_insights(report)
            report["optimization_opportunities"] = self._identify_optimization_opportunities(report)
            report["generated_at"] = datetime.now().isoformat()
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {"error": str(e)}
    
    # Helper methods
    
    def _get_available_images(self, campaign_type: str) -> List[str]:
        """Get list of available images for a campaign type"""
        # Import the image catalog from automation worker
        seaside_logo = "https://seasidesecurity.net/wp-content/uploads/2025/04/DLR.23.8.17-DealerComboLogo_SeasideSecurity_Horz_RGB_BlueGray-scaled-e1746532770501.webp"
        
        APPROVED_IMAGES = {
            'att_fiber': [
                "https://images.unsplash.com/photo-1606868306217-dbf5046868d2?w=600",
                "https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=600", 
                "https://images.unsplash.com/photo-1582201942988-13e60e4b31cd?w=600",
                "https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=600",
                "https://images.unsplash.com/photo-1551808525-51a94da548ce?w=600",
                "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=600",
                "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=600",
                "https://images.unsplash.com/photo-1504639725590-34d0984388bd?w=600"
            ],
            'adt_security': [
                seaside_logo,
                "https://images.unsplash.com/photo-1558618047-3c8f28cd2ca5?w=600", 
                "https://images.unsplash.com/photo-1609564403051-d3ae8ef8efaf?w=600",
                "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=600"
            ],
            'incident_alert': [
                seaside_logo,
                "https://images.unsplash.com/photo-1558618047-3c8f28cd2ca5?w=600",
                "https://images.unsplash.com/photo-1609564403051-d3ae8ef8efaf?w=600"
            ]
        }
        
        return APPROVED_IMAGES.get(campaign_type, APPROVED_IMAGES.get('att_fiber', []))
    
    def _get_image_performance(self, image_url: str, campaign_type: str) -> ImagePerformanceData:
        """Get performance data for a specific image"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM image_performance 
                WHERE image_url = ? AND campaign_type = ?
            ''', (image_url, campaign_type))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return ImagePerformanceData(
                    image_url=result[1],
                    campaign_type=result[2],
                    total_sends=result[5],
                    total_opens=result[6],
                    total_clicks=result[7],
                    open_rate=result[9],
                    click_rate=result[10],
                    conversion_rate=result[11],
                    engagement_score=result[12],
                    last_used=result[4]
                )
            else:
                return ImagePerformanceData(image_url=image_url, campaign_type=campaign_type)
                
        except Exception as e:
            logger.error(f"Error getting image performance: {e}")
            return ImagePerformanceData(image_url=image_url, campaign_type=campaign_type)
    
    def _get_fallback_image(self, campaign_type: str) -> str:
        """Get fallback image when optimization fails"""
        available = self._get_available_images(campaign_type)
        return available[0] if available else "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=600"
    
    def _update_image_performance(self, **kwargs):
        """Update image performance in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO image_performance 
                (image_url, campaign_type, campaign_id, timestamp, emails_sent, opens, clicks, conversions, 
                 open_rate, click_rate, conversion_rate, engagement_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                kwargs['image_url'], kwargs['campaign_type'], kwargs.get('campaign_id'),
                datetime.now().isoformat(), kwargs['emails_sent'], kwargs['opens'],
                kwargs['clicks'], kwargs['conversions'], kwargs['open_rate'],
                kwargs['click_rate'], kwargs['conversion_rate'], kwargs['engagement_score']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error updating image performance: {e}")
    
    def _generate_performance_insights(self, image_url: str, campaign_type: str, 
                                     open_rate: float, click_rate: float, engagement_score: float) -> List[str]:
        """Generate AI insights about image performance"""
        insights = []
        
        # Benchmark comparisons
        if open_rate > 0.25:
            insights.append(f"🎯 Excellent open rate ({open_rate:.1%}) - image creates strong first impression")
        elif open_rate < 0.15:
            insights.append(f"⚠️ Below-average open rate ({open_rate:.1%}) - consider different imagery")
        
        if click_rate > 0.08:
            insights.append(f"🚀 High click rate ({click_rate:.1%}) - image drives strong engagement")
        elif click_rate < 0.03:
            insights.append(f"📉 Low click rate ({click_rate:.1%}) - image may not compel action")
        
        # Image-specific insights
        if "seasidesecurity.net" in image_url:
            insights.append("🏢 Company branding builds trust and credibility")
        elif "fiber" in campaign_type and "office" in image_url:
            insights.append("💼 Home office imagery resonates well with remote work trends")
        elif "security" in campaign_type:
            insights.append("🔒 Security imagery effectively communicates protection value")
        
        # Performance tier classification
        if engagement_score > 0.12:
            insights.append("⭐ Top-tier performer - excellent choice for this campaign type")
        elif engagement_score < 0.05:
            insights.append("🔍 Under-performer - consider rotation or replacement")
        
        return insights
    
    def _load_performance_data(self):
        """Load performance data from database"""
        try:
            if os.path.exists(self.db_path):
                logger.info("✅ Image performance database loaded")
            else:
                logger.info("📊 Creating new image performance database")
        except Exception as e:
            logger.error(f"Error loading performance data: {e}")
    
    def _log_image_selection(self, image_url: str, campaign_type: str, strategy_data: Dict):
        """Log image selection for tracking"""
        logger.info(f"🖼️ Selected image for {campaign_type}: {image_url[-30:]}... (Strategy: {strategy_data['strategy']})")


if __name__ == "__main__":
    # Test the service
    service = AIImageOptimizationService()
    
    # Test optimal image selection
    image, strategy = service.get_optimal_image("att_fiber", audience_size=100)
    print(f"Selected image: {image[-50:]}...")
    print(f"Strategy: {strategy}")
    
    # Test A/B test creation
    ab_test = service.create_ab_test_campaign("att_fiber", audience_size=200)
    print(f"A/B test created: {ab_test.get('test_id', 'Error')}") 