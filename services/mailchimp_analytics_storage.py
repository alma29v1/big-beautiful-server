"""
Mailchimp Analytics Local Storage Service
Stores all Mailchimp campaign and audience data locally for AI analysis and historical tracking
"""

import sqlite3
import json
import os
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class MailchimpAnalyticsStorage:
    """Local storage system for Mailchimp analytics and campaign data"""
    
    def __init__(self, db_path: str = "data/analytics/mailchimp_analytics.db"):
        self.db_path = db_path
        self.ensure_database_directory()
        self.init_database()
        
    def ensure_database_directory(self):
        """Ensure the analytics directory exists"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
    def init_database(self):
        """Initialize the SQLite database with all necessary tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Campaigns table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS campaigns (
                        id TEXT PRIMARY KEY,
                        mailchimp_id TEXT UNIQUE,
                        type TEXT,
                        status TEXT,
                        subject_line TEXT,
                        preview_text TEXT,
                        from_name TEXT,
                        reply_to TEXT,
                        list_id TEXT,
                        list_name TEXT,
                        send_time TIMESTAMP,
                        emails_sent INTEGER,
                        abuse_reports INTEGER,
                        unsubscribed INTEGER,
                        hard_bounces INTEGER,
                        soft_bounces INTEGER,
                        syntax_errors INTEGER,
                        forwards_count INTEGER,
                        forwards_opens INTEGER,
                        opens INTEGER,
                        unique_opens INTEGER,
                        open_rate REAL,
                        clicks INTEGER,
                        unique_clicks INTEGER,
                        click_rate REAL,
                        subscriber_clicks INTEGER,
                        content_html TEXT,
                        content_text TEXT,
                        tags TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        raw_data TEXT
                    )
                ''')
                
                # Audiences/Lists table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS audiences (
                        id TEXT PRIMARY KEY,
                        mailchimp_id TEXT UNIQUE,
                        name TEXT,
                        contact_count INTEGER,
                        unsubscribe_count INTEGER,
                        cleaned_count INTEGER,
                        member_count INTEGER,
                        avg_sub_rate REAL,
                        avg_unsub_rate REAL,
                        target_sub_rate REAL,
                        open_rate REAL,
                        click_rate REAL,
                        date_created TIMESTAMP,
                        permission_reminder TEXT,
                        use_archive_bar BOOLEAN,
                        campaign_defaults TEXT,
                        notify_on_subscribe TEXT,
                        notify_on_unsubscribe TEXT,
                        list_rating REAL,
                        email_type_option BOOLEAN,
                        subscribe_url_short TEXT,
                        subscribe_url_long TEXT,
                        beamer_address TEXT,
                        visibility TEXT,
                        double_optin BOOLEAN,
                        has_welcome BOOLEAN,
                        marketing_permissions BOOLEAN,
                        tags TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        deleted_at TIMESTAMP,
                        raw_data TEXT
                    )
                ''')
                
                # Campaign Performance History table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS campaign_performance_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        campaign_id TEXT,
                        snapshot_date TIMESTAMP,
                        emails_sent INTEGER,
                        opens INTEGER,
                        unique_opens INTEGER,
                        open_rate REAL,
                        clicks INTEGER,
                        unique_clicks INTEGER,
                        click_rate REAL,
                        unsubscribes INTEGER,
                        bounces INTEGER,
                        forwards INTEGER,
                        abuse_reports INTEGER,
                        revenue REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
                    )
                ''')
                
                # Audience Members table (for detailed tracking)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS audience_members (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        audience_id TEXT,
                        email_address TEXT,
                        email_hash TEXT,
                        status TEXT,
                        merge_fields TEXT,
                        interests TEXT,
                        stats TEXT,
                        ip_signup TEXT,
                        timestamp_signup TIMESTAMP,
                        ip_opt TIMESTAMP,
                        timestamp_opt TIMESTAMP,
                        member_rating INTEGER,
                        last_changed TIMESTAMP,
                        language TEXT,
                        vip BOOLEAN,
                        email_client TEXT,
                        location TEXT,
                        marketing_permissions TEXT,
                        last_note TEXT,
                        list_id TEXT,
                        tags TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (audience_id) REFERENCES audiences (id)
                    )
                ''')
                
                # AI Insights table (for storing AI analysis)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ai_insights (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        entity_type TEXT,  -- 'campaign', 'audience', 'performance'
                        entity_id TEXT,
                        insight_type TEXT,  -- 'recommendation', 'trend', 'prediction'
                        insight_title TEXT,
                        insight_content TEXT,
                        confidence_score REAL,
                        data_points TEXT,  -- JSON of supporting data
                        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP,
                        is_active BOOLEAN DEFAULT 1
                    )
                ''')
                
                # Campaign Content Archive table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS campaign_content_archive (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        campaign_id TEXT,
                        content_type TEXT,  -- 'html', 'text', 'template'
                        content_data TEXT,
                        subject_variations TEXT,  -- JSON array of A/B test subjects
                        performance_by_variation TEXT,  -- JSON of performance data
                        archived_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
                    )
                ''')
                
                conn.commit()
                logger.info("Mailchimp analytics database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing analytics database: {e}")
            raise
    
    def store_campaign(self, campaign_data: Dict[str, Any]) -> bool:
        """Store or update campaign data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Extract campaign information
                campaign_id = campaign_data.get('id', '')
                settings = campaign_data.get('settings', {})
                recipients = campaign_data.get('recipients', {})
                report_summary = campaign_data.get('report_summary', {})
                
                # Prepare data for insertion
                campaign_record = {
                    'id': f"local_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{campaign_id}",
                    'mailchimp_id': campaign_id,
                    'type': campaign_data.get('type', ''),
                    'status': campaign_data.get('status', ''),
                    'subject_line': settings.get('subject_line', ''),
                    'preview_text': settings.get('preview_text', ''),
                    'from_name': settings.get('from_name', ''),
                    'reply_to': settings.get('reply_to', ''),
                    'list_id': recipients.get('list_id', ''),
                    'list_name': recipients.get('list_name', ''),
                    'send_time': campaign_data.get('send_time', ''),
                    'emails_sent': report_summary.get('emails_sent', 0),
                    'abuse_reports': report_summary.get('abuse_reports', 0),
                    'unsubscribed': report_summary.get('unsubscribed', 0),
                    'hard_bounces': report_summary.get('bounces', {}).get('hard_bounces', 0),
                    'soft_bounces': report_summary.get('bounces', {}).get('soft_bounces', 0),
                    'syntax_errors': report_summary.get('bounces', {}).get('syntax_errors', 0),
                    'forwards_count': report_summary.get('forwards', {}).get('forwards_count', 0),
                    'forwards_opens': report_summary.get('forwards', {}).get('forwards_opens', 0),
                    'opens': report_summary.get('opens', {}).get('opens_total', 0),
                    'unique_opens': report_summary.get('opens', {}).get('unique_opens', 0),
                    'open_rate': report_summary.get('opens', {}).get('open_rate', 0.0),
                    'clicks': report_summary.get('clicks', {}).get('clicks_total', 0),
                    'unique_clicks': report_summary.get('clicks', {}).get('unique_clicks', 0),
                    'click_rate': report_summary.get('clicks', {}).get('click_rate', 0.0),
                    'subscriber_clicks': report_summary.get('clicks', {}).get('unique_subscriber_clicks', 0),
                    'content_html': '',  # Will be populated separately
                    'content_text': '',  # Will be populated separately
                    'tags': json.dumps(campaign_data.get('tags', [])),
                    'raw_data': json.dumps(campaign_data)
                }
                
                # Insert or replace campaign
                placeholders = ', '.join(['?' for _ in campaign_record.keys()])
                columns = ', '.join(campaign_record.keys())
                
                cursor.execute(f'''
                    INSERT OR REPLACE INTO campaigns ({columns})
                    VALUES ({placeholders})
                ''', list(campaign_record.values()))
                
                # Store performance snapshot
                self._store_performance_snapshot(cursor, campaign_record['id'], report_summary)
                
                conn.commit()
                logger.info(f"Stored campaign data for: {campaign_record['subject_line']}")
                return True
                
        except Exception as e:
            logger.error(f"Error storing campaign data: {e}")
            return False
    
    def store_audience(self, audience_data: Dict[str, Any], mark_deleted: bool = False) -> bool:
        """Store or update audience data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Extract audience information
                audience_id = audience_data.get('id', '')
                stats = audience_data.get('stats', {})
                campaign_defaults = audience_data.get('campaign_defaults', {})
                
                # Prepare data for insertion
                audience_record = {
                    'id': f"local_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{audience_id}",
                    'mailchimp_id': audience_id,
                    'name': audience_data.get('name', ''),
                    'contact_count': stats.get('member_count', 0),
                    'unsubscribe_count': stats.get('unsubscribe_count', 0),
                    'cleaned_count': stats.get('cleaned_count', 0),
                    'member_count': stats.get('member_count', 0),
                    'avg_sub_rate': stats.get('avg_sub_rate', 0.0),
                    'avg_unsub_rate': stats.get('avg_unsub_rate', 0.0),
                    'target_sub_rate': stats.get('target_sub_rate', 0.0),
                    'open_rate': stats.get('open_rate', 0.0),
                    'click_rate': stats.get('click_rate', 0.0),
                    'date_created': audience_data.get('date_created', ''),
                    'permission_reminder': audience_data.get('permission_reminder', ''),
                    'use_archive_bar': audience_data.get('use_archive_bar', False),
                    'campaign_defaults': json.dumps(campaign_defaults),
                    'notify_on_subscribe': audience_data.get('notify_on_subscribe', ''),
                    'notify_on_unsubscribe': audience_data.get('notify_on_unsubscribe', ''),
                    'list_rating': stats.get('list_rating', 0.0),
                    'email_type_option': audience_data.get('email_type_option', False),
                    'subscribe_url_short': audience_data.get('subscribe_url_short', ''),
                    'subscribe_url_long': audience_data.get('subscribe_url_long', ''),
                    'beamer_address': audience_data.get('beamer_address', ''),
                    'visibility': audience_data.get('visibility', ''),
                    'double_optin': audience_data.get('double_optin', False),
                    'has_welcome': audience_data.get('has_welcome', False),
                    'marketing_permissions': audience_data.get('marketing_permissions', False),
                    'tags': json.dumps(audience_data.get('tags', [])),
                    'deleted_at': datetime.now().isoformat() if mark_deleted else None,
                    'raw_data': json.dumps(audience_data)
                }
                
                # Insert or replace audience
                placeholders = ', '.join(['?' for _ in audience_record.keys()])
                columns = ', '.join(audience_record.keys())
                
                cursor.execute(f'''
                    INSERT OR REPLACE INTO audiences ({columns})
                    VALUES ({placeholders})
                ''', list(audience_record.values()))
                
                conn.commit()
                logger.info(f"Stored audience data for: {audience_record['name']}")
                return True
                
        except Exception as e:
            logger.error(f"Error storing audience data: {e}")
            return False
    
    def _store_performance_snapshot(self, cursor, campaign_id: str, report_summary: Dict[str, Any]):
        """Store a performance snapshot for historical tracking"""
        try:
            snapshot_data = {
                'campaign_id': campaign_id,
                'snapshot_date': datetime.now().isoformat(),
                'emails_sent': report_summary.get('emails_sent', 0),
                'opens': report_summary.get('opens', {}).get('opens_total', 0),
                'unique_opens': report_summary.get('opens', {}).get('unique_opens', 0),
                'open_rate': report_summary.get('opens', {}).get('open_rate', 0.0),
                'clicks': report_summary.get('clicks', {}).get('clicks_total', 0),
                'unique_clicks': report_summary.get('clicks', {}).get('unique_clicks', 0),
                'click_rate': report_summary.get('clicks', {}).get('click_rate', 0.0),
                'unsubscribes': report_summary.get('unsubscribed', 0),
                'bounces': report_summary.get('bounces', {}).get('hard_bounces', 0) + 
                          report_summary.get('bounces', {}).get('soft_bounces', 0),
                'forwards': report_summary.get('forwards', {}).get('forwards_count', 0),
                'abuse_reports': report_summary.get('abuse_reports', 0),
                'revenue': 0.0  # Can be populated if ecommerce tracking is enabled
            }
            
            placeholders = ', '.join(['?' for _ in snapshot_data.keys()])
            columns = ', '.join(snapshot_data.keys())
            
            cursor.execute(f'''
                INSERT INTO campaign_performance_history ({columns})
                VALUES ({placeholders})
            ''', list(snapshot_data.values()))
            
        except Exception as e:
            logger.error(f"Error storing performance snapshot: {e}")
    
    def get_campaign_analytics(self, campaign_id: Optional[str] = None, days_back: int = 30) -> Dict[str, Any]:
        """Get comprehensive campaign analytics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Base query
                base_query = '''
                    SELECT * FROM campaigns 
                    WHERE created_at >= datetime('now', '-{} days')
                '''.format(days_back)
                
                if campaign_id:
                    base_query += f" AND (id = '{campaign_id}' OR mailchimp_id = '{campaign_id}')"
                
                base_query += " ORDER BY created_at DESC"
                
                cursor.execute(base_query)
                campaigns = [dict(row) for row in cursor.fetchall()]
                
                # Get performance trends
                performance_query = '''
                    SELECT 
                        DATE(snapshot_date) as date,
                        AVG(open_rate) as avg_open_rate,
                        AVG(click_rate) as avg_click_rate,
                        SUM(emails_sent) as total_emails,
                        SUM(opens) as total_opens,
                        SUM(clicks) as total_clicks
                    FROM campaign_performance_history 
                    WHERE snapshot_date >= datetime('now', '-{} days')
                    GROUP BY DATE(snapshot_date)
                    ORDER BY date DESC
                '''.format(days_back)
                
                cursor.execute(performance_query)
                performance_trends = [dict(row) for row in cursor.fetchall()]
                
                # Calculate summary statistics
                if campaigns:
                    total_campaigns = len(campaigns)
                    avg_open_rate = sum(c['open_rate'] or 0 for c in campaigns) / total_campaigns
                    avg_click_rate = sum(c['click_rate'] or 0 for c in campaigns) / total_campaigns
                    total_emails_sent = sum(c['emails_sent'] or 0 for c in campaigns)
                    total_opens = sum(c['opens'] or 0 for c in campaigns)
                    total_clicks = sum(c['clicks'] or 0 for c in campaigns)
                else:
                    total_campaigns = avg_open_rate = avg_click_rate = 0
                    total_emails_sent = total_opens = total_clicks = 0
                
                return {
                    'summary': {
                        'total_campaigns': total_campaigns,
                        'avg_open_rate': round(avg_open_rate, 4),
                        'avg_click_rate': round(avg_click_rate, 4),
                        'total_emails_sent': total_emails_sent,
                        'total_opens': total_opens,
                        'total_clicks': total_clicks,
                        'date_range': f"Last {days_back} days"
                    },
                    'campaigns': campaigns,
                    'performance_trends': performance_trends,
                    'generated_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting campaign analytics: {e}")
            return {'error': str(e)}
    
    def get_audience_analytics(self, audience_id: Optional[str] = None, include_deleted: bool = True) -> Dict[str, Any]:
        """Get comprehensive audience analytics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Base query
                base_query = "SELECT * FROM audiences"
                conditions = []
                
                if not include_deleted:
                    conditions.append("deleted_at IS NULL")
                
                if audience_id:
                    conditions.append(f"(id = '{audience_id}' OR mailchimp_id = '{audience_id}')")
                
                if conditions:
                    base_query += " WHERE " + " AND ".join(conditions)
                
                base_query += " ORDER BY created_at DESC"
                
                cursor.execute(base_query)
                audiences = [dict(row) for row in cursor.fetchall()]
                
                # Calculate summary statistics
                if audiences:
                    active_audiences = [a for a in audiences if not a['deleted_at']]
                    total_active = len(active_audiences)
                    total_deleted = len(audiences) - total_active
                    
                    if active_audiences:
                        avg_member_count = sum(a['member_count'] or 0 for a in active_audiences) / total_active
                        avg_open_rate = sum(a['open_rate'] or 0 for a in active_audiences) / total_active
                        avg_click_rate = sum(a['click_rate'] or 0 for a in active_audiences) / total_active
                        total_members = sum(a['member_count'] or 0 for a in active_audiences)
                    else:
                        avg_member_count = avg_open_rate = avg_click_rate = total_members = 0
                else:
                    total_active = total_deleted = 0
                    avg_member_count = avg_open_rate = avg_click_rate = total_members = 0
                
                return {
                    'summary': {
                        'total_active_audiences': total_active,
                        'total_deleted_audiences': total_deleted,
                        'avg_member_count': round(avg_member_count, 0),
                        'avg_open_rate': round(avg_open_rate, 4),
                        'avg_click_rate': round(avg_click_rate, 4),
                        'total_members': total_members
                    },
                    'audiences': audiences,
                    'generated_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting audience analytics: {e}")
            return {'error': str(e)}
    
    def store_ai_insight(self, entity_type: str, entity_id: str, insight_type: str, 
                        title: str, content: str, confidence: float = 0.8, 
                        data_points: Dict[str, Any] = None, expires_hours: int = 168) -> bool:
        """Store AI-generated insights for future reference"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                expires_at = datetime.now() + timedelta(hours=expires_hours)
                
                cursor.execute('''
                    INSERT INTO ai_insights 
                    (entity_type, entity_id, insight_type, insight_title, insight_content, 
                     confidence_score, data_points, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (entity_type, entity_id, insight_type, title, content, 
                      confidence, json.dumps(data_points or {}), expires_at.isoformat()))
                
                conn.commit()
                logger.info(f"Stored AI insight: {title}")
                return True
                
        except Exception as e:
            logger.error(f"Error storing AI insight: {e}")
            return False
    
    def get_ai_insights(self, entity_type: Optional[str] = None, entity_id: Optional[str] = None,
                       include_expired: bool = False) -> List[Dict[str, Any]]:
        """Get AI insights for analysis"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = "SELECT * FROM ai_insights WHERE is_active = 1"
                params = []
                
                if not include_expired:
                    query += " AND (expires_at IS NULL OR expires_at > datetime('now'))"
                
                if entity_type:
                    query += " AND entity_type = ?"
                    params.append(entity_type)
                
                if entity_id:
                    query += " AND entity_id = ?"
                    params.append(entity_id)
                
                query += " ORDER BY generated_at DESC"
                
                cursor.execute(query, params)
                insights = [dict(row) for row in cursor.fetchall()]
                
                # Parse JSON data_points
                for insight in insights:
                    try:
                        insight['data_points'] = json.loads(insight['data_points'] or '{}')
                    except:
                        insight['data_points'] = {}
                
                return insights
                
        except Exception as e:
            logger.error(f"Error getting AI insights: {e}")
            return []
    
    def export_analytics_data(self, format_type: str = 'json', output_path: Optional[str] = None) -> str:
        """Export all analytics data to specified format"""
        try:
            if not output_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = f"data/analytics/export_mailchimp_analytics_{timestamp}.{format_type}"
            
            # Ensure export directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Get all data
            campaigns = self.get_campaign_analytics(days_back=365)
            audiences = self.get_audience_analytics(include_deleted=True)
            insights = self.get_ai_insights(include_expired=True)
            
            export_data = {
                'export_metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'format': format_type,
                    'version': '1.0'
                },
                'campaigns': campaigns,
                'audiences': audiences,
                'ai_insights': insights
            }
            
            if format_type.lower() == 'json':
                with open(output_path, 'w') as f:
                    json.dump(export_data, f, indent=2, default=str)
            
            elif format_type.lower() == 'csv':
                # Export each table as separate CSV
                base_path = output_path.replace('.csv', '')
                
                if campaigns.get('campaigns'):
                    pd.DataFrame(campaigns['campaigns']).to_csv(f"{base_path}_campaigns.csv", index=False)
                
                if audiences.get('audiences'):
                    pd.DataFrame(audiences['audiences']).to_csv(f"{base_path}_audiences.csv", index=False)
                
                if insights:
                    pd.DataFrame(insights).to_csv(f"{base_path}_insights.csv", index=False)
            
            elif format_type.lower() == 'xlsx':
                with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                    if campaigns.get('campaigns'):
                        pd.DataFrame(campaigns['campaigns']).to_excel(writer, sheet_name='Campaigns', index=False)
                    
                    if audiences.get('audiences'):
                        pd.DataFrame(audiences['audiences']).to_excel(writer, sheet_name='Audiences', index=False)
                    
                    if insights:
                        pd.DataFrame(insights).to_excel(writer, sheet_name='AI_Insights', index=False)
            
            logger.info(f"Analytics data exported to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error exporting analytics data: {e}")
            return ""
    
    def cleanup_old_data(self, retention_days: int = 365):
        """Clean up old data based on retention policy"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cutoff_date = datetime.now() - timedelta(days=retention_days)
                
                # Clean up old performance snapshots
                cursor.execute('''
                    DELETE FROM campaign_performance_history 
                    WHERE snapshot_date < ?
                ''', (cutoff_date.isoformat(),))
                
                # Clean up expired AI insights
                cursor.execute('''
                    DELETE FROM ai_insights 
                    WHERE expires_at IS NOT NULL AND expires_at < datetime('now')
                ''', )
                
                conn.commit()
                logger.info(f"Cleaned up data older than {retention_days} days")
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics and health information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Table counts
                tables = ['campaigns', 'audiences', 'campaign_performance_history', 
                         'audience_members', 'ai_insights', 'campaign_content_archive']
                
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    stats[f"{table}_count"] = cursor.fetchone()[0]
                
                # Database size
                cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                db_size = cursor.fetchone()[0]
                stats['database_size_mb'] = round(db_size / (1024 * 1024), 2)
                
                # Recent activity
                cursor.execute("SELECT COUNT(*) FROM campaigns WHERE created_at >= datetime('now', '-7 days')")
                stats['recent_campaigns'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM audiences WHERE created_at >= datetime('now', '-7 days')")
                stats['recent_audiences'] = cursor.fetchone()[0]
                
                stats['last_updated'] = datetime.now().isoformat()
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {'error': str(e)} 