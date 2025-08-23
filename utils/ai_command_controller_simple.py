#!/usr/bin/env python3
"""
AI Command Controller (Simple Version)

This module provides AI-powered control over all program functions.
Users can use voice or text commands to control automation, incidents, campaigns, etc.
"""

import re
import time
import threading
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

@dataclass
class CommandResult:
    """Result of command execution"""
    success: bool
    message: str
    data: Optional[Any] = None
    action_taken: str = ""

class AICommandController:
    """AI-powered program controller with voice and text command support"""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.command_history = []
        self.system_status = {}
        self.setup_commands()
        
    def setup_commands(self):
        """Setup command patterns and actions"""
        self.commands = {
            # Automation Commands
            'run_automation': {
                'patterns': [
                    'run automation', 'start automation', 'execute automation',
                    'run the automation', 'start the automation', 'execute the automation',
                    'run full automation', 'start full automation', 'run complete automation'
                ],
                'description': 'Runs the complete automation workflow (Redfin, AT&T Fiber, BatchData, MailChimp)',
                'action': self.run_full_automation
            },
            
            'run_redfin': {
                'patterns': [
                    'run redfin', 'start redfin', 'pull redfin', 'get redfin data',
                    'run redfin pull', 'start redfin pull', 'pull redfin data'
                ],
                'description': 'Pulls Redfin property data',
                'action': self.run_redfin_pull
            },
            
            'check_fiber': {
                'patterns': [
                    'check fiber', 'check at&t fiber', 'check att fiber',
                    'run fiber check', 'start fiber check', 'check fiber availability',
                    'at&t fiber check', 'att fiber check'
                ],
                'description': 'Checks AT&T Fiber availability for addresses',
                'action': self.check_att_fiber
            },
            
            'process_batchdata': {
                'patterns': [
                    'process batchdata', 'run batchdata', 'start batchdata',
                    'process batch data', 'run batch data', 'enrich contacts'
                ],
                'description': 'Processes BatchData to enrich contact information',
                'action': self.process_batchdata
            },
            
            # Incident Commands
            'pull_incidents': {
                'patterns': [
                    'pull incidents', 'get incidents', 'load incidents',
                    'pull incident reports', 'get incident reports', 'load incident reports',
                    'check incidents', 'find incidents'
                ],
                'description': 'Pulls and loads incident reports',
                'action': self.pull_incident_reports
            },
            
            'send_incident_emails': {
                'patterns': [
                    'send incident emails', 'send emails to incidents', 'email incidents',
                    'send incident campaigns', 'generate incident emails', 'email incident contacts'
                ],
                'description': 'Generates and sends email campaigns to incident contacts',
                'action': self.send_incident_emails
            },
            
            'generate_incident_campaigns': {
                'patterns': [
                    'generate incident campaigns', 'create incident campaigns',
                    'make incident campaigns', 'build incident campaigns'
                ],
                'description': 'Generates email campaigns for incident contacts',
                'action': self.generate_incident_campaigns
            },
            
            # Contact Commands
            'load_contacts': {
                'patterns': [
                    'load contacts', 'get contacts', 'select contacts',
                    'load leads', 'get leads', 'select leads',
                    'load contact data', 'get contact data'
                ],
                'description': 'Loads contact/lead data',
                'action': self.load_contact_data
            },
            
            'generate_campaigns': {
                'patterns': [
                    'generate campaigns', 'create campaigns', 'make campaigns',
                    'generate email campaigns', 'create email campaigns',
                    'generate campaigns from leads', 'create campaigns from leads'
                ],
                'description': 'Generates email campaigns from loaded contacts',
                'action': self.generate_campaigns_from_leads
            },
            
            'send_campaigns': {
                'patterns': [
                    'send campaigns', 'send to mailchimp', 'upload to mailchimp',
                    'send email campaigns', 'upload campaigns', 'send to mailchimp'
                ],
                'description': 'Sends campaigns to MailChimp',
                'action': self.send_campaigns_to_mailchimp
            },
            
            # Analytics Commands
            'show_analytics': {
                'patterns': [
                    'show analytics', 'display analytics', 'get analytics',
                    'show performance', 'display performance', 'get performance',
                    'show stats', 'display stats', 'get stats'
                ],
                'description': 'Shows campaign analytics and performance',
                'action': self.show_analytics
            },
            
            'export_reports': {
                'patterns': [
                    'export reports', 'export data', 'download reports',
                    'export analytics', 'download analytics', 'save reports'
                ],
                'description': 'Exports reports and analytics data',
                'action': self.export_reports
            },
            
            # System Commands
            'system_status': {
                'patterns': [
                    'system status', 'show status', 'get status',
                    'what is running', 'what is active', 'current status'
                ],
                'description': 'Shows current system status',
                'action': self.get_system_status
            },
            
            'help': {
                'patterns': [
                    'help', 'show help', 'what can you do', 'available commands',
                    'list commands', 'show commands', 'what commands'
                ],
                'description': 'Shows available commands and help',
                'action': self.show_help
            }
        }
    
    def parse_command(self, user_input: str) -> Tuple[str, str, Optional[Dict]]:
        """Parse user input and map to program actions"""
        input_lower = user_input.lower().strip()
        
        # Check for exact matches first
        for command_name, command_info in self.commands.items():
            for pattern in command_info['patterns']:
                if pattern in input_lower:
                    return command_name, user_input, command_info
        
        # Check for partial matches
        for command_name, command_info in self.commands.items():
            for pattern in command_info['patterns']:
                pattern_words = pattern.split()
                input_words = input_lower.split()
                
                # Check if most words match
                matches = sum(1 for word in pattern_words if any(word in input_word for input_word in input_words))
                if matches >= len(pattern_words) * 0.7:  # 70% match threshold
                    return command_name, user_input, command_info
        
        return 'unknown', user_input, None
    
    def is_command(self, user_input: str) -> bool:
        """Check if input is a command"""
        command_name, _, _ = self.parse_command(user_input)
        return command_name != 'unknown'
    
    def execute_command(self, user_input: str) -> CommandResult:
        """Execute the parsed command"""
        command_name, original_input, command_info = self.parse_command(user_input)
        
        # Log command
        self.command_history.append({
            'timestamp': time.time(),
            'input': original_input,
            'command': command_name
        })
        
        if command_name == 'unknown':
            return CommandResult(
                success=False,
                message="I don't understand that command. Say 'help' to see available commands.",
                action_taken="none"
            )
        
        try:
            # Execute the command
            print(f"🔄 Executing: {command_info['description']}")
            
            result = command_info['action']()
            
            # Update system status
            self.update_system_status()
            
            return CommandResult(
                success=True,
                message=f"✅ {result}",
                action_taken=command_name
            )
            
        except Exception as e:
            error_msg = f"❌ Error executing {command_name}: {str(e)}"
            print(error_msg)
            
            return CommandResult(
                success=False,
                message=error_msg,
                action_taken=command_name
            )
    
    # Automation Commands
    def run_full_automation(self) -> str:
        """Execute the full automation workflow"""
        try:
            # Start automation
            if hasattr(self.main_window, 'start_automation'):
                self.main_window.start_automation()
                return "Full automation started successfully! This will run Redfin pull, AT&T Fiber check, BatchData processing, and MailChimp upload."
            else:
                return "Automation function not available in main window."
        except Exception as e:
            raise Exception(f"Failed to start automation: {str(e)}")
    
    def run_redfin_pull(self) -> str:
        """Run Redfin data pull"""
        try:
            if hasattr(self.main_window, 'start_redfin_pull'):
                self.main_window.start_redfin_pull()
                return "Redfin data pull started successfully!"
            else:
                return "Redfin pull function not available."
        except Exception as e:
            raise Exception(f"Failed to start Redfin pull: {str(e)}")
    
    def check_att_fiber(self) -> str:
        """Check AT&T Fiber availability"""
        try:
            if hasattr(self.main_window, 'start_att_fiber_check'):
                self.main_window.start_att_fiber_check()
                return "AT&T Fiber check started successfully!"
            else:
                return "AT&T Fiber check function not available."
        except Exception as e:
            raise Exception(f"Failed to start AT&T Fiber check: {str(e)}")
    
    def process_batchdata(self) -> str:
        """Process BatchData"""
        try:
            if hasattr(self.main_window, 'start_batchdata_processing'):
                self.main_window.start_batchdata_processing()
                return "BatchData processing started successfully!"
            else:
                return "BatchData processing function not available."
        except Exception as e:
            raise Exception(f"Failed to start BatchData processing: {str(e)}")
    
    # Incident Commands
    def pull_incident_reports(self) -> str:
        """Pull and display incident reports"""
        try:
            if hasattr(self.main_window, 'check_for_real_incidents'):
                self.main_window.check_for_real_incidents()
                return "Incident reports pulled successfully! Check the incidents tab for details."
            else:
                return "Incident monitoring function not available."
        except Exception as e:
            raise Exception(f"Failed to pull incidents: {str(e)}")
    
    def send_incident_emails(self) -> str:
        """Send emails to incident contacts"""
        try:
            if hasattr(self.main_window, 'generate_incident_campaigns_from_contacts'):
                self.main_window.generate_incident_campaigns_from_contacts()
                return "Incident emails generated and sent successfully!"
            else:
                return "Incident email function not available."
        except Exception as e:
            raise Exception(f"Failed to send incident emails: {str(e)}")
    
    def generate_incident_campaigns(self) -> str:
        """Generate campaigns for incidents"""
        try:
            if hasattr(self.main_window, 'generate_incident_campaigns_from_contacts'):
                self.main_window.generate_incident_campaigns_from_contacts()
                return "Incident campaigns generated successfully!"
            else:
                return "Incident campaign generation function not available."
        except Exception as e:
            raise Exception(f"Failed to generate incident campaigns: {str(e)}")
    
    # Contact Commands
    def load_contact_data(self) -> str:
        """Load contact data"""
        try:
            if hasattr(self.main_window, 'select_existing_leads'):
                self.main_window.select_existing_leads()
                return "Contact data loaded successfully!"
            else:
                return "Contact loading function not available."
        except Exception as e:
            raise Exception(f"Failed to load contacts: {str(e)}")
    
    def generate_campaigns_from_leads(self) -> str:
        """Generate campaigns from leads"""
        try:
            if hasattr(self.main_window, 'generate_campaigns_from_leads'):
                self.main_window.generate_campaigns_from_leads()
                return "Campaigns generated from leads successfully!"
            else:
                return "Campaign generation function not available."
        except Exception as e:
            raise Exception(f"Failed to generate campaigns: {str(e)}")
    
    def send_campaigns_to_mailchimp(self) -> str:
        """Send campaigns to MailChimp"""
        try:
            if hasattr(self.main_window, 'send_campaigns_to_mailchimp'):
                self.main_window.send_campaigns_to_mailchimp()
                return "Campaigns sent to MailChimp successfully!"
            else:
                return "MailChimp sending function not available."
        except Exception as e:
            raise Exception(f"Failed to send campaigns: {str(e)}")
    
    # Analytics Commands
    def show_analytics(self) -> str:
        """Show analytics"""
        try:
            if hasattr(self.main_window, 'load_analytics'):
                self.main_window.load_analytics()
                return "Analytics loaded successfully! Check the analytics tab."
            else:
                return "Analytics function not available."
        except Exception as e:
            raise Exception(f"Failed to load analytics: {str(e)}")
    
    def export_reports(self) -> str:
        """Export reports"""
        try:
            if hasattr(self.main_window, 'export_analytics'):
                self.main_window.export_analytics()
                return "Reports exported successfully!"
            else:
                return "Export function not available."
        except Exception as e:
            raise Exception(f"Failed to export reports: {str(e)}")
    
    # System Commands
    def get_system_status(self) -> str:
        """Get current system status"""
        try:
            status = {
                'automation_running': getattr(self.main_window, 'automation_active', False),
                'contacts_loaded': len(getattr(self.main_window, 'contacts', [])),
                'incidents_found': len(getattr(self.main_window, 'incidents', [])),
                'campaigns_ready': len(getattr(self.main_window, 'campaigns', [])),
                'last_command': self.command_history[-1]['command'] if self.command_history else 'None'
            }
            
            status_text = f"System Status:\n"
            status_text += f"• Automation Running: {'Yes' if status['automation_running'] else 'No'}\n"
            status_text += f"• Contacts Loaded: {status['contacts_loaded']}\n"
            status_text += f"• Incidents Found: {status['incidents_found']}\n"
            status_text += f"• Campaigns Ready: {status['campaigns_ready']}\n"
            status_text += f"• Last Command: {status['last_command']}"
            
            return status_text
        except Exception as e:
            raise Exception(f"Failed to get system status: {str(e)}")
    
    def show_help(self) -> str:
        """Show available commands and help"""
        help_text = "Available Commands:\n\n"
        
        for command_name, command_info in self.commands.items():
            help_text += f"🎯 {command_info['description']}\n"
            help_text += f"   Examples: {', '.join(command_info['patterns'][:3])}\n\n"
        
        help_text += "💡 Tips:\n"
        help_text += "• You can use voice or text commands\n"
        help_text += "• Commands are flexible - try different ways to say the same thing\n"
        help_text += "• Say 'system status' to check what's running\n"
        help_text += "• Say 'help' anytime to see this list again"
        
        return help_text
    
    def update_system_status(self):
        """Update system status"""
        try:
            self.system_status = {
                'last_update': time.time(),
                'automation_running': getattr(self.main_window, 'automation_active', False),
                'contacts_loaded': len(getattr(self.main_window, 'contacts', [])),
                'incidents_found': len(getattr(self.main_window, 'incidents', [])),
                'campaigns_ready': len(getattr(self.main_window, 'campaigns', [])),
                'command_count': len(self.command_history)
            }
        except Exception as e:
            print(f"Error updating system status: {e}")

print("✅ AI Command Controller (Simple) loaded successfully!") 