#!/usr/bin/env python3
"""
AI Command Controller

This module provides AI-powered control over all program functions.
Users can use voice or text commands to control automation, incidents, campaigns, etc.
"""

import re
import time
import threading
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtWidgets import QMessageBox

@dataclass
class CommandResult:
    """Result of command execution"""
    success: bool
    message: str
    data: Optional[Any] = None
    action_taken: str = ""

class AICommandController(QObject):
    """AI-powered program controller with voice and text command support"""
    
    # Signals for UI updates
    command_executed = Signal(str, str)  # action, result
    status_updated = Signal(str)  # status message
    error_occurred = Signal(str)  # error message
    
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.command_history = []
        self.system_status = {}
        self.premium_voice = None
        self.setup_commands()
        self.setup_premium_voice()
        
    def setup_premium_voice(self):
        """Setup premium voice system"""
        try:
            from utils.premium_voice_system import premium_voice
            self.premium_voice = premium_voice
            print("✅ Premium voice system loaded")
        except Exception as e:
            print(f"⚠️ Premium voice system not available: {e}")
            self.premium_voice = None
        
    def setup_commands(self):
        """Setup command patterns and actions"""
        self.commands = {
            # Automation Commands
            'run_automation': {
                'patterns': [
                    'run automation', 'start automation', 'execute automation',
                    'run the automation', 'start the automation', 'execute the automation',
                    'run full automation', 'start full automation', 'run complete automation',
                    'can you run the automation', 'please run automation', 'run automation for me'
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
            
            # Marketing Commands
            'marketing_strategies': {
                'patterns': [
                    'marketing strategies', 'your marketing strategies', 'marketing strategy',
                    'email marketing strategies', 'campaign strategies', 'marketing ideas',
                    'what would you like to discuss', 'discuss marketing'
                ],
                'description': 'Discusses marketing strategies and campaign ideas',
                'action': self.discuss_marketing_strategies
            },
            
            'help': {
                'patterns': [
                    'help', 'show help', 'commands', 'show commands', 'what can you do',
                    'available commands', 'help me', 'assistance'
                ],
                'description': 'Shows available commands and help information',
                'action': self.show_help
            },
            
            # Voice Commands
            'change_voice': {
                'patterns': [
                    'change voice', 'switch voice', 'different voice', 'new voice',
                    'set voice', 'voice options', 'available voices'
                ],
                'description': 'Changes the voice for text-to-speech',
                'action': self.change_voice
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
                'description': 'Generates email campaigns from incident data',
                'action': self.generate_incident_campaigns
            },
            
            # Contact Commands
            'load_contact_data': {
                'patterns': [
                    'load contact data', 'load contacts', 'import contacts',
                    'get contact data', 'load contact information'
                ],
                'description': 'Loads contact data from various sources',
                'action': self.load_contact_data
            },
            
            'generate_campaigns_from_leads': {
                'patterns': [
                    'generate campaigns from leads', 'create campaigns from leads',
                    'make campaigns from leads', 'build campaigns from leads'
                ],
                'description': 'Generates email campaigns from lead data',
                'action': self.generate_campaigns_from_leads
            },
            
            'send_campaigns_to_mailchimp': {
                'patterns': [
                    'send campaigns to mailchimp', 'upload to mailchimp',
                    'send to mailchimp', 'mailchimp upload'
                ],
                'description': 'Sends campaigns to MailChimp',
                'action': self.send_campaigns_to_mailchimp
            },
            
            # Analytics Commands
            'show_analytics': {
                'patterns': [
                    'show analytics', 'display analytics', 'view analytics',
                    'analytics', 'performance', 'statistics'
                ],
                'description': 'Shows analytics and performance data',
                'action': self.show_analytics
            },
            
            'export_reports': {
                'patterns': [
                    'export reports', 'download reports', 'save reports',
                    'generate reports', 'create reports'
                ],
                'description': 'Exports reports and data',
                'action': self.export_reports
            },
            
            # System Commands
            'get_system_status': {
                'patterns': [
                    'system status', 'status', 'check status', 'system info',
                    'what is the status', 'how is the system'
                ],
                'description': 'Shows system status and information',
                'action': self.get_system_status
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
            # Try to provide a helpful response for unknown commands
            response = self.generate_helpful_response(original_input)
            return CommandResult(
                success=False,
                message=response,
                action_taken="none"
            )
        
        try:
            # Execute the command
            self.status_updated.emit(f"🔄 Executing: {command_info['description']}")
            
            result = command_info['action']()
            
            # Update system status
            self.update_system_status()
            
            # Speak the result if premium voice is available
            if self.premium_voice and result:
                self.premium_voice.speak_async(result)
            
            return CommandResult(
                success=True,
                message=f"✅ {result}",
                action_taken=command_name
            )
            
        except Exception as e:
            error_msg = f"❌ Error executing {command_name}: {str(e)}"
            self.error_occurred.emit(error_msg)
            
            return CommandResult(
                success=False,
                message=error_msg,
                action_taken=command_name
            )
    
    def generate_helpful_response(self, user_input: str) -> str:
        """Generate a helpful response for unknown commands"""
        input_lower = user_input.lower()
        
        # Check for common patterns and provide helpful responses
        if any(word in input_lower for word in ['marketing', 'strategy', 'strategies']):
            return "I can help you with marketing strategies! Try saying 'marketing strategies' to discuss email marketing, AT&T Fiber campaigns, or ADT Security promotions. Or say 'help' to see all available commands."
        
        if any(word in input_lower for word in ['automation', 'run', 'start', 'execute']):
            return "I can run automation for you! Try saying 'run automation' to start the complete workflow, or 'help' to see all available automation commands."
        
        if any(word in input_lower for word in ['voice', 'speak', 'talk']):
            return "I can change voices for you! Try saying 'change voice' to switch to a different voice, or 'help' to see all available commands."
        
        # Default helpful response
        return f"I understand you said: '{user_input}'. I'm here to help with automation, marketing strategies, and campaign management. Say 'help' to see all available commands, or try asking about 'marketing strategies' or 'run automation'."
    
    # Marketing Commands
    def discuss_marketing_strategies(self) -> str:
        """Discuss marketing strategies"""
        strategies = [
            "📧 Email Marketing Campaigns: Create targeted campaigns for AT&T Fiber and ADT Security",
            "🎯 Lead Generation: Use Redfin data to find potential customers",
            "📊 Analytics & Optimization: Track campaign performance and optimize results",
            "🤖 AI-Powered Content: Generate compelling email content automatically",
            "📱 Multi-Channel Marketing: Combine email, social media, and direct outreach"
        ]
        
        response = "Here are some powerful marketing strategies we can work on:\n\n"
        response += "\n".join(strategies)
        response += "\n\nWhat would you like to focus on? I can help you create campaigns, analyze data, or optimize your marketing efforts."
        
        return response
    
    def change_voice(self) -> str:
        """Change the voice for text-to-speech"""
        if not self.premium_voice:
            return "Premium voice system not available. Using default system voice."
        
        try:
            voices = self.premium_voice.get_available_voices()
            voice_list = list(voices.keys())
            
            # Cycle to next voice
            current_voice = self.premium_voice.current_voice
            current_index = voice_list.index(current_voice) if current_voice in voice_list else 0
            next_index = (current_index + 1) % len(voice_list)
            new_voice = voice_list[next_index]
            
            self.premium_voice.set_voice(new_voice)
            voice_info = voices[new_voice]
            
            return f"Voice changed to {voice_info['name']} ({voice_info['quality']} quality). This voice will be used for all responses."
            
        except Exception as e:
            return f"Error changing voice: {str(e)}"
    
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
                return "AT&T Fiber availability check started successfully!"
            else:
                return "AT&T Fiber check function not available."
        except Exception as e:
            raise Exception(f"Failed to start AT&T Fiber check: {str(e)}")
    
    def process_batchdata(self) -> str:
        """Process BatchData to enrich contacts"""
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
        """Pull and load incident reports"""
        try:
            if hasattr(self.main_window, 'pull_incidents'):
                self.main_window.pull_incidents()
                return "Incident reports pulled successfully!"
            else:
                return "Incident pull function not available."
        except Exception as e:
            raise Exception(f"Failed to pull incidents: {str(e)}")
    
    def send_incident_emails(self) -> str:
        """Generate and send incident email campaigns"""
        try:
            if hasattr(self.main_window, 'send_incident_emails'):
                self.main_window.send_incident_emails()
                return "Incident email campaigns generated and sent successfully!"
            else:
                return "Incident email function not available."
        except Exception as e:
            raise Exception(f"Failed to send incident emails: {str(e)}")
    
    def generate_incident_campaigns(self) -> str:
        """Generate email campaigns from incident data"""
        try:
            if hasattr(self.main_window, 'generate_incident_campaigns'):
                self.main_window.generate_incident_campaigns()
                return "Incident campaigns generated successfully!"
            else:
                return "Incident campaign generation function not available."
        except Exception as e:
            raise Exception(f"Failed to generate incident campaigns: {str(e)}")
    
    # Contact Commands
    def load_contact_data(self) -> str:
        """Load contact data from various sources"""
        try:
            if hasattr(self.main_window, 'load_contacts'):
                self.main_window.load_contacts()
                return "Contact data loaded successfully!"
            else:
                return "Contact loading function not available."
        except Exception as e:
            raise Exception(f"Failed to load contacts: {str(e)}")
    
    def generate_campaigns_from_leads(self) -> str:
        """Generate email campaigns from lead data"""
        try:
            if hasattr(self.main_window, 'generate_campaigns_from_leads'):
                self.main_window.generate_campaigns_from_leads()
                return "Campaigns generated from leads successfully!"
            else:
                return "Lead campaign generation function not available."
        except Exception as e:
            raise Exception(f"Failed to generate campaigns from leads: {str(e)}")
    
    def send_campaigns_to_mailchimp(self) -> str:
        """Send campaigns to MailChimp"""
        try:
            if hasattr(self.main_window, 'send_to_mailchimp'):
                self.main_window.send_to_mailchimp()
                return "Campaigns sent to MailChimp successfully!"
            else:
                return "MailChimp send function not available."
        except Exception as e:
            raise Exception(f"Failed to send to MailChimp: {str(e)}")
    
    # Analytics Commands
    def show_analytics(self) -> str:
        """Show analytics and performance data"""
        try:
            if hasattr(self.main_window, 'show_analytics'):
                self.main_window.show_analytics()
                return "Analytics displayed successfully!"
            else:
                return "Analytics function not available."
        except Exception as e:
            raise Exception(f"Failed to show analytics: {str(e)}")
    
    def export_reports(self) -> str:
        """Export reports and data"""
        try:
            if hasattr(self.main_window, 'export_reports'):
                self.main_window.export_reports()
                return "Reports exported successfully!"
            else:
                return "Export function not available."
        except Exception as e:
            raise Exception(f"Failed to export reports: {str(e)}")
    
    # System Commands
    def get_system_status(self) -> str:
        """Show system status and information"""
        try:
            self.update_system_status()
            
            status_info = []
            for key, value in self.system_status.items():
                status_info.append(f"• {key}: {value}")
            
            if status_info:
                return "System Status:\n" + "\n".join(status_info)
            else:
                return "System status information not available."
        except Exception as e:
            raise Exception(f"Failed to get system status: {str(e)}")
    
    def show_help(self) -> str:
        """Show available commands and help information"""
        help_text = "🤖 AI Command Controller - Available Commands:\n\n"
        
        # Group commands by category
        categories = {
            "🎯 Marketing": ['marketing_strategies'],
            "🚀 Automation": ['run_automation', 'run_redfin', 'check_fiber', 'process_batchdata'],
            "📊 Analytics": ['show_analytics', 'export_reports'],
            "📧 Campaigns": ['send_incident_emails', 'generate_incident_campaigns', 'send_campaigns_to_mailchimp'],
            "📋 Data": ['pull_incidents', 'load_contact_data', 'generate_campaigns_from_leads'],
            "🎤 Voice": ['change_voice'],
            "ℹ️ System": ['get_system_status', 'help']
        }
        
        for category, command_names in categories.items():
            help_text += f"{category}:\n"
            for cmd_name in command_names:
                if cmd_name in self.commands:
                    cmd_info = self.commands[cmd_name]
                    help_text += f"  • {cmd_info['description']}\n"
            help_text += "\n"
        
        help_text += "💡 Tips:\n"
        help_text += "• You can use voice or text commands\n"
        help_text += "• Try saying 'marketing strategies' to discuss campaigns\n"
        help_text += "• Say 'run automation' to start the complete workflow\n"
        help_text += "• Use 'change voice' to switch to different voice options\n"
        
        return help_text
    
    def update_system_status(self):
        """Update system status information"""
        try:
            self.system_status = {
                "Commands Executed": len(self.command_history),
                "Last Command": self.command_history[-1]['command'] if self.command_history else "None",
                "Voice System": "Premium" if self.premium_voice else "Standard",
                "Available Commands": len(self.commands)
            }
        except Exception as e:
            print(f"Error updating system status: {e}")

print("✅ AI Command Controller loaded successfully!") 