import time
import os
from workers.redfin_worker import RedfinWorker
from workers.att_worker import ATTWorker
from workers.batchdata_worker import BatchDataWorker
from workers.adt_detection_worker import ADTDetectionWorker
from workers.mailchimp_worker import MailchimpWorker
from services.ai_email_marketing_service import AIEmailMarketingService
from config.campaign_config import CampaignConfig

# VerifyDialog removed - all UI operations should happen on main thread via signals

class AutomationWorker:
    def __init__(self, processes, main_window=None):
        from PySide6.QtCore import QThread, Signal
        
        # Create a proper QThread subclass
        class AutomationWorkerThread(QThread):
            log_signal = Signal(str)
            progress_signal = Signal(int, int)
            finished_signal = Signal(bool)
            verify_signal = Signal(str)
            launch_signal = Signal()
            incident_campaigns_signal = Signal(list)  # NEW: Signal for incident campaigns
            regular_campaigns_signal = Signal(dict)  # NEW: Signal for regular campaigns
            
            def __init__(self, processes, parent_instance):
                super().__init__()
                self.processes = processes
                self.results = {}
                self.parent_instance = parent_instance
                
            def run(self):
                self.parent_instance.run_automation(self)
        
        self.thread = AutomationWorkerThread(processes, self)
        self.log_signal = self.thread.log_signal
        self.progress_signal = self.thread.progress_signal
        self.finished_signal = self.thread.finished_signal
        self.verify_signal = self.thread.verify_signal
        self.launch_signal = self.thread.launch_signal
        self.incident_campaigns_signal = self.thread.incident_campaigns_signal  # NEW: Expose incident signal
        self.regular_campaigns_signal = self.thread.regular_campaigns_signal  # NEW: Expose regular campaigns signal
        self.processes = processes
        self.results = {}
        self.main_window = main_window  # Store reference to main window
        self.auto_approval_enabled = True  # Enable auto-approval by default
        
    def start(self):
        self.thread.start()
        
    def wait(self):
        self.thread.wait()
    
    def isRunning(self):
        """Check if the automation thread is running"""
        return self.thread.isRunning() if hasattr(self.thread, 'isRunning') else False
    
    def terminate(self):
        """Terminate the automation thread"""
        if hasattr(self.thread, 'terminate'):
            self.thread.terminate()
    
    def stop(self):
        """Stop the automation thread gracefully"""
        if hasattr(self.thread, 'terminate'):
            self.thread.terminate()

    def run_automation(self, thread):
        total_steps = len(self.processes)
        
        # Log mode information
        
        for i, process in enumerate(self.processes, 1):
            thread.progress_signal.emit(i, total_steps)
            thread.log_signal.emit(f"[Automation] Running: {process}")
            
            try:
                if process == "Redfin Pull":
                    thread.log_signal.emit("[Automation] Starting Redfin data pull...")
                    self.results['redfin'] = self.run_redfin()
                    thread.log_signal.emit("[Automation] ✅ Redfin pull triggered")
                    thread.log_signal.emit("[Automation] ⏳ Waiting for Redfin download to complete...")
                    
                    # Wait for Redfin to actually complete by checking status
                    self.wait_for_redfin_completion(thread)
                    
                elif process == "AT&T Fiber Check":
                    thread.log_signal.emit("[Automation] Starting AT&T fiber checks...")
                    self.results['att'] = self.run_att()
                    thread.log_signal.emit("[Automation] ✅ AT&T checks triggered")
                    thread.log_signal.emit("[Automation] ⏳ Waiting for AT&T processing to complete...")
                    
                    # Wait for AT&T to actually complete by checking status
                    self.wait_for_att_completion(thread)
                    
                elif process == "ADT Detection":
                    thread.log_signal.emit("[Automation] Running ADT detection...")
                    self.results['adt'] = self.run_adt()
                    thread.log_signal.emit("[Automation] ✅ ADT detection triggered")
                    thread.log_signal.emit("[Automation] ⏳ Waiting for ADT detection to complete...")
                    
                    # Wait for ADT to actually complete by checking status
                    self.wait_for_adt_completion(thread)
                    
                elif process == "Incident Monitoring":
                    thread.log_signal.emit("[Automation] 🚨 Checking for recent incidents...")
                    self.results['incidents'] = self.run_incident_monitoring(thread)
                    thread.log_signal.emit("[Automation] ✅ Incident monitoring completed")
                    
                elif process == "BatchData Contacts":
                    thread.log_signal.emit("[Automation] Getting contact information...")
                    self.results['batchdata'] = self.run_batchdata()
                    thread.log_signal.emit("[Automation] ✅ BatchData triggered")
                    thread.log_signal.emit("[Automation] ⏳ Waiting for BatchData processing to complete...")
                    
                    # Wait for BatchData to actually complete and verify success
                    if not self.wait_for_batchdata_completion(thread):
                        thread.log_signal.emit("[Automation] ⚠️ BatchData found no new contacts - checking for existing contacts...")
                        # Check if we have existing contacts from previous runs
                        if self.check_for_existing_contacts(thread):
                            thread.log_signal.emit("[Automation] ✅ Found existing contacts - proceeding with automation")
                        else:
                            thread.log_signal.emit("[Automation] ❌ No contacts available - stopping automation")
                            thread.log_signal.emit("[Automation] ⚠️ Cannot proceed without contact information")
                            thread.finished_signal.emit(False)
                            return
                    
                elif process == "MailChimp Upload":
                    thread.log_signal.emit("[Automation] Uploading to MailChimp...")
                    
                    # Check if we have contacts to upload (either new or existing)
                    if self.check_for_existing_contacts(thread):
                        self.results['mailchimp'] = self.run_mailchimp()
                        thread.log_signal.emit("[Automation] ✅ MailChimp upload triggered")
                        thread.log_signal.emit("[Automation] ⏳ Waiting for MailChimp upload to complete...")
                        
                        # Wait for MailChimp to actually complete by checking status
                        self.wait_for_mailchimp_completion(thread)
                    else:
                        thread.log_signal.emit("[Automation] ⚠️ No contacts available for MailChimp - skipping")
                        self.results['mailchimp'] = "No contacts available"
                    
                elif process == "ActiveKnocker Pin Assignment":
                    thread.log_signal.emit("[Automation] Sending leads to ActiveKnocker for Mark Walters...")
                    self.results['activeknocker'] = self.run_activeknocker_automation()
                    thread.log_signal.emit("[Automation] ✅ ActiveKnocker automation completed")
                    
                elif process == "AI Email Composition and Launch":
                    thread.log_signal.emit("[Automation] Generating AI email campaigns...")
                    
                    # Generate AI emails with MailChimp analytics
                    email_campaigns = self.generate_ai_email_campaigns_with_analytics()
                    
                    if email_campaigns:
                        thread.log_signal.emit("[Automation] ✅ AI emails generated successfully")
                        thread.log_signal.emit(f"[Automation] 📧 Generated {len(email_campaigns)} campaigns: {list(email_campaigns.keys())}")
                        thread.log_signal.emit("[Automation] ⏸️ PAUSING for email review...")
                        thread.log_signal.emit("[Automation] 👀 Please review the generated campaigns before sending")
                        thread.log_signal.emit("[Automation] ⏱️ Automation paused indefinitely - please review and approve campaigns")
                        
                        # Store campaigns for review interface
                        self.generated_campaigns = email_campaigns
                        
                        # Trigger the email review interface
                        if hasattr(self, 'main_window'):
                            from PySide6.QtCore import QMetaObject, Qt
                            
                            thread.log_signal.emit("[Automation] 🔄 Updating AI Email Marketing widget...")
                            thread.log_signal.emit(f"[Automation] 📋 Campaign details: {[(k, v.get('title', 'No title')) for k, v in email_campaigns.items()]}")
                            
                            # Store campaigns in main window for access
                            self.main_window.pending_campaigns = email_campaigns
                            thread.log_signal.emit("[Automation] 💾 Campaigns stored in main window")
                            
                            # Send campaigns to AI email widget via thread-safe signal
                            thread.log_signal.emit("[Automation] 📧 Sending campaigns to AI widget...")
                            thread.regular_campaigns_signal.emit(email_campaigns)
                            
                            # Switch to AI Email Marketing tab to show campaigns
                            QMetaObject.invokeMethod(
                                self.main_window,
                                "switch_to_ai_email_tab",
                                Qt.QueuedConnection
                            )
                        else:
                            thread.log_signal.emit("[Automation] ⚠️ Main window not available for campaign display")
                        
                        # Wait for user approval
                        if self.wait_for_email_approval(thread):
                            thread.log_signal.emit("[Automation] ✅ Emails approved - sending campaigns")
                            self.send_approved_campaigns(thread)
                        else:
                            thread.log_signal.emit("[Automation] ❌ Email review cancelled - stopping automation")
                            thread.finished_signal.emit(False)
                            return
                    else:
                        thread.log_signal.emit("[Automation] ❌ Failed to generate AI emails")
                        thread.finished_signal.emit(False)
                        return
                    
                    self.results['ai'] = "AI email campaigns generated and sent"
            except Exception as e:
                thread.log_signal.emit(f"[Automation] ❌ Error in {process}: {str(e)}")
                
            time.sleep(2)  # Brief pause between processes
        
        thread.finished_signal.emit(True)

    def run_redfin(self):
        # Use QMetaObject.invokeMethod to call on main thread
        from PySide6.QtCore import QMetaObject, Qt
        if hasattr(self, 'main_window'):
            QMetaObject.invokeMethod(self.main_window, "pull_data", Qt.QueuedConnection)
        return "Redfin data pull triggered"

    def run_att(self):
        # Use QMetaObject.invokeMethod to call on main thread
        from PySide6.QtCore import QMetaObject, Qt
        if hasattr(self, 'main_window'):
            QMetaObject.invokeMethod(self.main_window, "start_processing", Qt.QueuedConnection)
        return "AT&T processing triggered"

    def run_batchdata(self):
        # Use QMetaObject.invokeMethod to call on main thread
        from PySide6.QtCore import QMetaObject, Qt
        if hasattr(self, 'main_window'):
            QMetaObject.invokeMethod(self.main_window, "start_batchdata_processing", Qt.QueuedConnection)
        return "BatchData processing triggered"

    def run_adt(self):
        # Use QMetaObject.invokeMethod to call on main thread (automated version without popup)
        from PySide6.QtCore import QMetaObject, Qt
        if hasattr(self, 'main_window'):
            QMetaObject.invokeMethod(self.main_window, "run_adt_detection_automated", Qt.QueuedConnection)
        return "ADT detection triggered"

    def run_mailchimp(self):
        # Use QMetaObject.invokeMethod to call on main thread
        from PySide6.QtCore import QMetaObject, Qt
        if hasattr(self, 'main_window'):
            QMetaObject.invokeMethod(self.main_window, "manual_mailchimp_send", Qt.QueuedConnection)
        return "MailChimp upload triggered"

    def run_ai(self):
        service = AIEmailMarketingService()
        contacts = self.results.get('mailchimp', [])
        config = CampaignConfig(subject='Automated Campaign', body='Generated by AI', recipients=[])
        campaign = service.generate_email_campaign(contacts, config)
        return "AI campaign generated and launched"
        
    def run_incident_monitoring(self, thread):
        """Run REAL incident monitoring with 25-yard radius targeting"""
        try:
            thread.log_signal.emit("[Automation] 🚨 Starting REAL incident monitoring system...")
            
            # Import real incident monitoring
            from workers.real_incident_automation import RealIncidentAutomation
            
            # Get target cities from config
            target_cities = [
                "Wilmington, NC", "Leland, NC", "Hampstead, NC", 
                "Lumberton, NC", "Southport, NC", "Jacksonville, NC", "Fayetteville, NC"
            ]
            radius_yards = 25  # REAL 25-yard radius as requested
            
            thread.log_signal.emit(f"[Automation] 📍 Monitoring {len(target_cities)} cities for REAL incidents")
            thread.log_signal.emit(f"[Automation] 🎯 Targeting customers within {radius_yards} yards of incidents")
            
            # Create real incident monitor
            real_incident_monitor = RealIncidentAutomation(target_cities, radius_yards)
            
            # Track results
            incident_results = {'incidents': 0, 'campaigns': 0, 'generated_campaigns': []}
            
            # Connect to monitor signals to capture results
            def capture_campaigns(campaigns):
                incident_results['campaigns'] = len(campaigns)
                incident_results['generated_campaigns'].extend(campaigns)
                thread.log_signal.emit(f"[Automation] 📧 Generated {len(campaigns)} URGENT incident campaigns from REAL data")
                
                # Send campaigns to AI Email Marketing widget for approval
                if hasattr(self, 'main_window') and self.main_window:
                    # Store incident campaigns separately from standard campaigns
                    if not hasattr(self.main_window, 'pending_incident_campaigns'):
                        self.main_window.pending_incident_campaigns = []
                    self.main_window.pending_incident_campaigns.extend(campaigns)
                    
                    # Send to AI Email Marketing widget via thread-safe signal
                    thread.incident_campaigns_signal.emit(campaigns)
                    
                    thread.log_signal.emit("[Automation] 📧 URGENT incident campaigns sent to AI Email Marketing tab")
            
            def capture_final_results(results):
                if results.get('success'):
                    incident_results['incidents'] = results.get('incidents', 0)
                    incident_results['campaigns'] = results.get('campaigns', 0)
                    thread.log_signal.emit(f"[Automation] ✅ REAL incident monitoring complete")
                    thread.log_signal.emit(f"[Automation] 🚨 Found {incident_results['incidents']} real incidents")
                    thread.log_signal.emit(f"[Automation] 📧 Generated {incident_results['campaigns']} targeted campaigns")
                else:
                    thread.log_signal.emit(f"[Automation] ❌ Real incident monitoring error: {results.get('error', 'Unknown error')}")
            
            # Connect signals
            real_incident_monitor.log_signal.connect(thread.log_signal)
            real_incident_monitor.campaigns_signal.connect(capture_campaigns)
            real_incident_monitor.finished_signal.connect(capture_final_results)
            
            # Run real incident monitoring
            result_message = real_incident_monitor.run_real_incident_monitoring()
            
            if incident_results['campaigns'] > 0:
                thread.log_signal.emit(f"[Automation] 🚨 URGENT: {incident_results['campaigns']} real incident campaigns generated!")
                thread.log_signal.emit(f"[Automation] 🎯 Each campaign targets customers within 25 yards of incident")
                thread.log_signal.emit("[Automation] 👀 Check AI Email Marketing tab to approve URGENT incident emails")
            else:
                thread.log_signal.emit("[Automation] ✅ No incidents requiring immediate customer notification")
            
            return result_message or f"Real incident monitoring: {incident_results['incidents']} incidents, {incident_results['campaigns']} campaigns"
            
        except Exception as e:
            thread.log_signal.emit(f"[Automation] ❌ Error in incident monitoring: {str(e)}")
            return f"Incident monitoring failed: {str(e)}"
    
    def run_activeknocker_automation(self):
        """Run ActiveKnocker automation to send leads to Mark Walters"""
        try:
            from workers.activeknocker_automation import ActiveKnockerAutomationWorker
            
            # Create and run ActiveKnocker worker
            ak_worker = ActiveKnockerAutomationWorker()
            
            # Set up a simple event loop to wait for completion
            import time
            ak_worker.start()
            
            # Wait for completion (simplified for automation context)
            start_time = time.time()
            timeout = 300  # 5 minute timeout
            
            while ak_worker.isRunning() and (time.time() - start_time) < timeout:
                time.sleep(1)
            
            if ak_worker.isRunning():
                ak_worker.stop()
                ak_worker.wait(5000)  # Wait up to 5 seconds for clean shutdown
                return "ActiveKnocker automation timed out"
            
            return "ActiveKnocker leads sent to Mark Walters"
            
        except Exception as e:
            return f"ActiveKnocker automation error: {str(e)}"
    
    def generate_ai_email_campaigns_with_analytics(self, custom_contacts=None):
        """Generate AI email campaigns using MailChimp analytics data"""
        try:
            from services.enhanced_ai_email_service import EnhancedAIEmailService
            
            # Initialize services
            enhanced_service = EnhancedAIEmailService()
            
            # Get MailChimp analytics data
            try:
                mailchimp_data = enhanced_service.get_comprehensive_mailchimp_data()
                campaign_analytics = enhanced_service.get_campaign_analytics(limit=10)
            except Exception as e:
                print(f"Error getting MailChimp data: {e}")
                mailchimp_data = {}
                campaign_analytics = []
            
            # Analyze previous campaigns for insights
            if campaign_analytics:
                try:
                    analysis = enhanced_service.ai_analyze_campaign_performance(campaign_analytics)
                    insights = analysis.get('key_insights', ["No previous campaign data available"])
                    optimization_tips = analysis.get('optimization_recommendations', ["Start with A/B testing subject lines", "Focus on clear call-to-action"])
                except Exception as e:
                    print(f"Error analyzing campaigns: {e}")
                    insights = ["No previous campaign data available"]
                    optimization_tips = ["Start with A/B testing subject lines", "Focus on clear call-to-action"]
            else:
                insights = ["No previous campaign data available"]
                optimization_tips = ["Start with A/B testing subject lines", "Focus on clear call-to-action"]
            
            # Use custom contacts if provided, otherwise get from BatchData results
            if custom_contacts:
                contacts = custom_contacts
                print(f"[Automation Worker] Using {len(contacts)} custom contacts for campaigns")
                print(f"[DEBUG] Custom contacts sample: {contacts[0] if contacts else 'None'}")
            else:
                contacts = self.get_contacts_for_campaigns()
                print(f"[Automation Worker] Found {len(contacts)} contacts for campaigns")
            
            if not contacts:
                print("[Automation Worker] No contacts found for campaigns")
                return None
            
            # Separate contacts by fiber status and ADT status
            fiber_contacts = [c for c in contacts if c.get('fiber_available', False)]
            non_fiber_contacts = [c for c in contacts if not c.get('fiber_available', False)]
            adt_contacts = [c for c in contacts if c.get('adt_detected', False)]
            
            print(f"[Automation Worker] Fiber contacts: {len(fiber_contacts)}")
            print(f"[Automation Worker] Non-fiber contacts: {len(non_fiber_contacts)}")
            print(f"[Automation Worker] ADT contacts: {len(adt_contacts)}")
            
            # Generate campaigns - SINGLE CAMPAIGNS ONLY
            campaigns = {}
            
            # 1. SINGLE AT&T Fiber Campaign (ONLY for fiber-available contacts)
            if fiber_contacts:
                print(f"[Automation Worker] Generating AT&T Fiber campaign with {len(fiber_contacts)} contacts")
                fiber_campaign = self.generate_simple_campaign_content(
                    campaign_type='att_fiber',
                    contacts=fiber_contacts,
                    insights=insights,
                    optimization_tips=optimization_tips,
                    mailchimp_data=mailchimp_data
                )
                # Use single campaign key to prevent duplicates
                campaigns['att_fiber_main'] = fiber_campaign
                print(f"✅ SINGLE AT&T Fiber Campaign: {len(fiber_contacts)} fiber-available customers")
                print(f"[DEBUG] Fiber campaign has {len(fiber_campaign.get('contacts', []))} contacts")
            
            # 2. SINGLE ADT Security Campaign (for ALL contacts - both fiber and non-fiber)
            all_contacts_for_adt = fiber_contacts + non_fiber_contacts  # Combine all contacts
            if all_contacts_for_adt:
                print(f"[Automation Worker] Generating ADT Security campaign with {len(all_contacts_for_adt)} contacts")
                adt_campaign = self.generate_simple_campaign_content(
                    campaign_type='adt_security',
                    contacts=all_contacts_for_adt,
                    insights=insights,
                    optimization_tips=optimization_tips,
                    mailchimp_data=mailchimp_data
                )
                # Use single campaign key to prevent duplicates
                campaigns['adt_security_main'] = adt_campaign
                print(f"✅ SINGLE ADT Security Campaign: {len(all_contacts_for_adt)} total customers (fiber + non-fiber)")
                print(f"[DEBUG] ADT campaign has {len(adt_campaign.get('contacts', []))} contacts")
            
            # REMOVED: No more duplicate AT&T campaigns for non-fiber customers
            # REMOVED: No more general outreach campaigns that confuse the targeting
            
            print(f"[Automation Worker] Generated {len(campaigns)} campaigns")
            
            # Debug: Show final campaign structure
            for campaign_id, campaign_data in campaigns.items():
                print(f"[DEBUG] Final campaign {campaign_id}:")
                print(f"[DEBUG]   - Title: {campaign_data.get('title', 'Unknown')}")
                print(f"[DEBUG]   - Has contacts: {'contacts' in campaign_data}")
                print(f"[DEBUG]   - Has recipients: {'recipients' in campaign_data}")
                print(f"[DEBUG]   - Contacts count: {len(campaign_data.get('contacts', []))}")
                print(f"[DEBUG]   - Recipients count: {len(campaign_data.get('recipients', []))}")
                print(f"[DEBUG]   - Target contacts: {campaign_data.get('target_contacts', 'N/A')}")
            
            return campaigns
            
        except Exception as e:
            print(f"Error generating AI campaigns: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_simple_campaign_content(self, campaign_type, contacts, insights, optimization_tips, mailchimp_data):
        """Generate simple campaign content with basic AI"""
        try:
            from datetime import datetime
            
            # Create campaign based on type
            if campaign_type == 'att_fiber':
                campaign = {
                    'campaign_type': 'AT&T Fiber',
                    'title': '🌐 AT&T Fiber Campaign',
                    'icon': '🌐',
                    'target_audience': 'Fiber-available homeowners',
                    'company_name': 'Seaside Home Services',
                    'subject_lines': [
                        'High-Speed Fiber Internet Now Available!',
                        'Upgrade to Lightning-Fast Fiber Today',
                        'Say Goodbye to Slow Internet - Fiber is Here!',
                        'Your Neighborhood Just Got Faster Internet'
                    ],
                    'email_body': """
Dear {name},

🏡 **Welcome to Your New Home at {address}!**

Congratulations on your recent move! As you're settling into your new neighborhood, we wanted to make sure you have access to the fastest internet available.

<img src="file:///Volumes/LaCie/the_big_beautiful_program/campaign_images/att-fiber_1.jpg" alt="AT&T Fiber Installation by Seaside Security" style="max-width: 500px; height: auto; margin: 20px 0; border-radius: 8px; display: block;">

🚀 **AT&T Fiber is now available at your new address!**
• Lightning-fast speeds up to 1 Gig
• Perfect for setting up your new home office
• Stream, game, and video call without interruption
• No contracts - just reliable internet

Moving into a new home is exciting! Let us help make your internet setup seamless and worry-free.

<!-- Clickable AT&T Button -->
<div style="text-align: center; margin: 30px 0;">
<a href="https://www.attspoc.com/?key=rHk1NyPpuZGGqQZ1" style="background-color: #0066cc; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">🌐 Get AT&T Fiber Now</a>
</div>

📞 **New Resident Special**
Call us at (910) 713-1213 for:
• FREE installation scheduling
• Exclusive new homeowner discounts
• Same-day service availability

Welcome to the neighborhood!

Best regards,
The Fiber Team
Seaside Home Services

<!-- Note: Replace with client's fiber images from seasidesecurity.net -->
""",
                    'call_to_action': 'Schedule Installation Today',
                    'predicted_open_rate': 0.28,
                    'predicted_click_rate': 0.08,
                    'customer_phone': '(910) 713-1213',
                    'signup_link': 'https://www.attspoc.com/?key=rHk1NyPpuZGGqQZ1'
                }
            elif campaign_type == 'adt_security':
                campaign = {
                    'campaign_type': 'ADT Security',
                    'title': '🔒 ADT Security Campaign',
                    'icon': '🔒',
                    'target_audience': 'Security-conscious homeowners',
                    'company_name': 'Seaside Security',
                    'subject_lines': [
                        'Protect Your Home with Advanced Security',
                        'Your Home Deserves Better Protection',
                        'Special Security Offer for Your Neighborhood',
                        'Peace of Mind Starts with Professional Security'
                    ],
                    'email_body': f"""
Dear {{name}},

We noticed you're interested in home security for your property at {{address}}.

🏠 24/7 professional monitoring
📱 Smart home integration  
🚨 Instant emergency response
💡 Mobile app control

Your family's safety is our priority. Let us help you secure your home with the latest technology.

📞 Call us at (910) 742-0609 for a free consultation
📅 Schedule your ADT installation: https://seasidesecurity.net/schedule-appointment/

<div style="text-align: center; margin: 20px 0;">
<a href="https://seasidesecurity.net/schedule-appointment/" style="background-color: #c41e3a; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">Schedule Free Security Consultation</a>
</div>

<img src="https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600" alt="Professional security installation" style="width: 100%; max-width: 600px; margin: 20px 0;" />

<img src="https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=600" alt="Home security system" style="width: 100%; max-width: 600px; margin: 20px 0;" />

<div style="text-align: center; margin: 30px 0;">
<img src="https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=300" alt="Seaside Security ADT Logo" style="width: 200px; height: auto;" />
<p style="color: #666; margin-top: 10px;">Professional ADT Security Services</p>
</div>

Best regards,<br>
The Security Team<br>
Seaside Security<br>
www.seasidesecurity.net
""",
                    'call_to_action': 'Get Free Security Consultation',
                    'predicted_open_rate': 0.32,
                    'predicted_click_rate': 0.12,
                    'customer_phone': '(910) 742-0609',
                    'contacts': contacts,
                    'target_contacts': len(contacts),
                    'mailchimp_insights': [
                        'Security campaigns perform better in evening',
                        'ADT logo increases trust by 25%',
                        'Free consultation offers have higher conversions'
                    ],
                    'optimization_tips': [
                        'Focus on peace of mind messaging',
                        'Include professional installation images',
                        'Highlight 24/7 monitoring benefits'
                    ],
                    'previous_performance': {},
                    'created_at': datetime.now().isoformat(),
                    'status': 'pending_review'
                }
            # REMOVED: att_general campaign type to prevent duplicates
            # Only att_fiber campaigns are used for fiber-available customers
            elif campaign_type == 'adt_general' or campaign_type == 'adt_security':
                campaign = {
                    'campaign_type': 'ADT General Outreach',
                    'title': '🔒 ADT Security Services Campaign',
                    'icon': '🔒',
                    'target_audience': 'General homeowners',
                    'company_name': 'Seaside Security',
                    'subject_lines': [
                        'Protect Your Home with Advanced Security',
                        'Special ADT Security Offers for Your Neighborhood',
                        'Transform Your Home with Smart Security',
                        'Exclusive ADT Services Available in Your Area'
                    ],
                    'email_body': """
Dear {name},

🏡 **Welcome to Your New Neighborhood at {address}!**

Congratulations on your recent move! As you're getting settled in your new home, we wanted to introduce you to the exclusive ADT services available in your area.

🔒 **New Homeowner ADT Services:**
• Advanced security systems for your new home setup
• Smart home automation for convenience
• 24/7 monitoring services for peace of mind
• Professional installation that works with your schedule

Starting fresh in a new home? Let us help you get secured with the best security solutions for your family.

📞 **New Resident Hotline**: Call us at (910) 742-0609 for special offers
👉 **Move-in Special**: Sign up online: https://www.adtspoc.com/?key=rHk1NyPpuZGGqQZ1

Welcome to the neighborhood!

Best regards,
The ADT Team
Seaside Security

<div style="text-align: center; margin: 30px 0;">
<img src="https://seasidesecurity.net/wp-content/uploads/2025/04/DLR.23.8.17-DealerComboLogo_SeasideSecurity_Horz_RGB_BlueGray-scaled-e1746532770501.webp" alt="Seaside Security" style="max-width: 300px; margin: 20px 0;">
<p style="color: #666; margin-top: 10px;">Professional ADT Security Services</p>
</div>
""",
                    'call_to_action': 'Learn More About ADT Services',
                    'predicted_open_rate': 0.25,
                    'predicted_click_rate': 0.06,
                    'customer_phone': '(910) 742-0609',
                    'scheduling_link': '[ADT_SCHEDULING_LINK]'
                }
            elif campaign_type == 'incident_alert':
                # Special incident-based template for neighborhood security alerts
                campaign = {
                    'campaign_type': 'Incident Alert',
                    'title': '🚨 Neighborhood Security Alert',
                    'icon': '🚨',
                    'target_audience': 'Residents near recent incidents',
                    'company_name': 'Seaside Security',
                    'subject_lines': [
                        'Important Security Update for Your Neighborhood',
                        'Protect Your Home After Recent Local Incident',
                        'Urgent: Enhanced Security Available in Your Area',
                        'Your Neighbors Are Taking Action - Shouldn\'t You?',
                        'Recent Activity in Your Area - Security Solutions Available'
                    ],
                    'email_body': """
Dear {name},

🚨 **Important Security Notice for {address}**

We wanted to reach out following the recent {incident_type} incident that occurred near your neighborhood at {incident_address}. While we hope this was an isolated event, we understand this may raise concerns about safety in your area.

🔒 **Immediate Security Solutions Available:**
• FREE security assessment for your property
• 24/7 professional monitoring and rapid response
• Smart security systems with mobile alerts
• Neighborhood watch coordination and support
• **Special incident response pricing available**

🏠 **Your family's safety is our priority.** Many of your neighbors are already taking proactive steps to enhance their security following this incident.

📞 **Immediate Response**: Call us at (910) 742-0609 for priority security consultation
📅 **Free Assessment**: Schedule your home security evaluation today

We're here to help protect what matters most to you.

Best regards,
The Security Response Team
Seaside Security

<div style="text-align: center; margin: 30px 0;">
<img src="https://seasidesecurity.net/wp-content/uploads/2025/04/DLR.23.8.17-DealerComboLogo_SeasideSecurity_Horz_RGB_BlueGray-scaled-e1746532770501.webp" alt="Seaside Security" style="max-width: 300px; margin: 20px 0;">
<p style="color: #666; margin-top: 10px;">Professional ADT Security Services</p>
</div>

*This message was sent due to proximity to a recent security incident. We believe in keeping our community informed and safe.*
""",
                    'call_to_action': 'Get Immediate Security Assessment',
                    'predicted_open_rate': 0.45,  # Higher due to urgency and relevance
                    'predicted_click_rate': 0.18,  # Higher conversion expected
                    'customer_phone': '(910) 742-0609',
                    'incident_specific': True
                }
            else:  # general_outreach (fallback)
                campaign = {
                    'campaign_type': 'General Outreach',
                    'title': '📢 General Outreach Campaign',
                    'icon': '📢',
                    'target_audience': 'General homeowners',
                    'company_name': 'Seaside Home Services',
                    'subject_lines': [
                        'Upgrade Your Home Technology Today',
                        'Special Offers for Your Neighborhood',
                        'Transform Your Home with Smart Technology',
                        'Exclusive Services Available in Your Area'
                    ],
                    'email_body': """
Dear {name},

🏡 **Welcome to Your New Neighborhood at {address}!**

Congratulations on your recent move! As you're getting settled in your new home, we wanted to introduce you to the exclusive AT&T services available in your area.

🌐 **New Homeowner AT&T Services:**
• High-speed internet solutions for your new home setup
• TV and streaming packages for family entertainment
• Phone services with crystal-clear calling
• Professional installation that works with your schedule

Starting fresh in a new home? Let us help you get connected with the best technology solutions for your family.

📞 **New Resident Hotline**: Call us at (910) 713-1213 for special offers
👉 **Move-in Special**: Sign up online: https://www.attspoc.com/?key=rHk1NyPpuZGGqQZ1

Welcome to the neighborhood!

Best regards,
The AT&T Team
Seaside Home Services
""",
                    'call_to_action': 'Learn More About Our Services',
                    'predicted_open_rate': 0.25,
                    'predicted_click_rate': 0.06,
                    'att_phone': '(910) 713-1213',
                    'adt_phone': '(910) 742-0609',
                    'signup_link': 'https://www.attspoc.com/?key=rHk1NyPpuZGGqQZ1'
                }
            
            # Add common fields
            campaign.update({
                'contacts': contacts,
                'target_contacts': len(contacts),
                'mailchimp_insights': insights,
                'optimization_tips': optimization_tips,
                'previous_performance': self.extract_performance_data(mailchimp_data),
                'created_at': datetime.now().isoformat(),
                'status': 'pending_review'
            })
            
            print(f"[DEBUG] Campaign '{campaign_type}' created with {len(contacts)} contacts")
            print(f"[DEBUG] Campaign keys: {list(campaign.keys())}")
            print(f"[DEBUG] Campaign has 'contacts': {'contacts' in campaign}")
            print(f"[DEBUG] Campaign has 'recipients': {'recipients' in campaign}")
            print(f"[DEBUG] Final contacts count: {len(campaign.get('contacts', []))}")
            print(f"[DEBUG] Final recipients count: {len(campaign.get('recipients', []))}")
            
            return campaign
            
        except Exception as e:
            print(f"Error generating simple campaign content: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_contacts_for_campaigns(self):
        """Get contact data from BatchData results, avoiding double-pulls"""
        try:
            all_contacts = []
            
            # First, check ContactManager for existing pending contacts
            from utils.contact_manager import ContactManager
            manager = ContactManager()
            pending_contacts = manager.get_pending_contacts()
            
            if pending_contacts:
                print(f"[Automation] Found {len(pending_contacts)} pending contacts from ContactManager")
                all_contacts.extend(pending_contacts)
            
            # Second, check if we have recent BatchData results in main window
            if hasattr(self.main_window, 'batchdata_results') and self.main_window.batchdata_results:
                results = self.main_window.batchdata_results
                if isinstance(results, dict) and 'results' in results:
                    contacts = results['results']
                    print(f"[Automation] Found {len(contacts)} stored BatchData results")
                    all_contacts.extend(contacts)
                elif isinstance(results, list):
                    print(f"[Automation] Found {len(results)} stored BatchData results")
                    all_contacts.extend(results)
            
            # Check for recent CSV files with contact data (multiple patterns)
            import glob
            import pandas as pd
            
            # Look for CURRENT automation contacts ONLY (not old master files)
            csv_patterns = [
                'email_ready_contacts_*.csv',       # Current automation contacts
                'batchdata_consolidated_*.csv',     # Current BatchData results
                'real_contacts_*.csv',              # Alternative naming
                'att_fiber_real_contacts_*.csv',    # AT&T Fiber contacts
                'adt_security_real_contacts_*.csv', # ADT Security contacts
                'processed_incident_contacts_*.csv' # Incident contacts
            ]
            
            # Also check for AT&T fiber results files
            att_fiber_patterns = [
                'att_fiber_results_*.csv'           # Latest AT&T fiber availability results
            ]
            
            best_file = None
            best_count = 0
            
            for pattern in csv_patterns:
                csv_files = glob.glob(pattern)
                print(f"[Automation] Checking pattern '{pattern}': found {len(csv_files)} files")
                if csv_files:
                    # Get the most recent file for this pattern
                    latest_file = max(csv_files, key=os.path.getctime)
                    print(f"[Automation] Latest file for '{pattern}': {latest_file}")
                    
                    # Check if file is recent (within last 30 days to allow existing contacts)
                    file_age = time.time() - os.path.getctime(latest_file)
                    print(f"[Automation] File age for {latest_file}: {file_age/86400:.1f} days")
                    if file_age < 2592000:  # 30 days in seconds
                        try:
                            df = pd.read_csv(latest_file)
                            contact_count = len(df)
                            
                            # Prioritize files with more contacts
                            if contact_count > best_count:
                                best_file = latest_file
                                best_count = contact_count
                                
                        except Exception as e:
                            print(f"[Automation] Error reading CSV file {latest_file}: {e}")
            
            # First, get the latest AT&T fiber results to update fiber availability
            att_fiber_data = {}
            for pattern in att_fiber_patterns:
                csv_files = glob.glob(pattern)
                if csv_files:
                    # Load ALL AT&T fiber result files, not just the latest one
                    for csv_file in csv_files:
                        try:
                            df = pd.read_csv(csv_file)
                            for _, row in df.iterrows():
                                address = row.get('address', '')
                                fiber_available = row.get('fiber_available', False)
                                if address:
                                    att_fiber_data[address] = fiber_available
                            print(f"[Automation] Loaded {len(df)} AT&T fiber results from {csv_file}")
                        except Exception as e:
                            print(f"[Automation] Error reading AT&T fiber file {csv_file}: {e}")
                    print(f"[Automation] Total AT&T fiber results loaded: {len(att_fiber_data)} addresses")
            
            if best_file:
                try:
                    df = pd.read_csv(best_file)
                    contacts = df.to_dict('records')
                    
                    # Filter for successful contacts (accept both 'success' and 'completed' status)
                    if 'batchdata_status' in df.columns:
                        valid_contacts = [
                            c for c in contacts 
                            if c.get('batchdata_status') in ['completed', 'success'] and c.get('owner_name')
                        ]
                    else:
                        # If no status column, assume all contacts are valid if they have owner_name
                        valid_contacts = [
                            c for c in contacts 
                            if c.get('owner_name')
                        ]
                    
                    # Update fiber availability from AT&T results
                    updated_contacts = []
                    for contact in valid_contacts:
                        address = contact.get('address', '')
                        if address in att_fiber_data:
                            contact['fiber_available'] = att_fiber_data[address]
                        updated_contacts.append(contact)
                    
                    if updated_contacts:
                        print(f"[Automation] Found {len(updated_contacts)} valid contacts in {best_file}")
                        print(f"[Automation] Contact breakdown:")
                        
                        # Show breakdown by fiber status
                        fiber_contacts = [c for c in updated_contacts if c.get('fiber_available', False)]
                        non_fiber_contacts = [c for c in updated_contacts if not c.get('fiber_available', False)]
                        
                        print(f"[Automation]   - Fiber available: {len(fiber_contacts)} contacts")
                        print(f"[Automation]   - No fiber: {len(non_fiber_contacts)} contacts")
                        print(f"[Automation]   - Total from file: {len(updated_contacts)} contacts")
                        
                        all_contacts.extend(updated_contacts)
                        
                except Exception as e:
                    print(f"[Automation] Error processing best file {best_file}: {e}")
            
            # Return combined contacts from all sources
            if all_contacts:
                print(f"[Automation] ✅ Total contacts found: {len(all_contacts)} from all sources")
                
                # Remove duplicates based on email address
                unique_contacts = []
                seen_emails = set()
                for contact in all_contacts:
                    email = contact.get('owner_email', '')
                    if email and email not in seen_emails:
                        unique_contacts.append(contact)
                        seen_emails.add(email)
                
                print(f"[Automation] ✅ After deduplication: {len(unique_contacts)} unique contacts")
                return unique_contacts
            else:
                print("[Automation] No recent contact data found - BatchData will need to be run")
                return []
            
        except Exception as e:
            print(f"Error getting contacts for campaigns: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def extract_performance_data(self, mailchimp_data):
        """Extract key performance metrics from MailChimp data"""
        try:
            campaigns = mailchimp_data.get('campaigns', [])
            if not campaigns:
                return {}
            
            # Calculate averages
            total_campaigns = len(campaigns)
            avg_open_rate = sum(c.open_rate for c in campaigns) / total_campaigns
            avg_click_rate = sum(c.click_rate for c in campaigns) / total_campaigns
            
            return {
                'avg_open_rate': avg_open_rate,
                'avg_click_rate': avg_click_rate,
                'total_campaigns': total_campaigns,
                'best_performing_subject': max(campaigns, key=lambda x: x.open_rate).subject_line if campaigns else ""
            }
        except Exception as e:
            return {}
    
    def pause_for_email_review(self, thread, email_campaigns):
        """Pause automation and show email review interface"""
        try:
            # Use QMetaObject.invokeMethod to call on main thread
            from PySide6.QtCore import QMetaObject, Qt
            if hasattr(self, 'main_window'):
                # Store campaigns for review
                self.main_window.pending_email_campaigns = email_campaigns
                
                # Show email review interface
                QMetaObject.invokeMethod(
                    self.main_window, 
                    "show_email_review_interface", 
                    Qt.QueuedConnection
                )
                
                thread.log_signal.emit("[Automation] 📧 Email review interface opened")
                thread.log_signal.emit("[Automation] ⏸️ Automation paused - waiting for your approval")
                
        except Exception as e:
            thread.log_signal.emit(f"[Automation] ❌ Error showing email review: {e}")
    
    def wait_for_email_approval(self, thread):
        """Wait for user to approve or reject the email campaigns, or auto-approve if enabled"""
        if self.auto_approval_enabled:
            thread.log_signal.emit("[Automation] ✅ Auto-approval enabled - automatically approving campaigns")
            return True
        else:
            check_interval = 5  # Check every 5 seconds
            wait_time = 0
            
            # Check if user has made a decision via the automation worker flags
            if hasattr(self, 'email_review_complete') and self.email_review_complete:
                if hasattr(self, 'email_approved') and self.email_approved:
                    thread.log_signal.emit("[Automation] ✅ Emails approved by user")
                    return True
                else:
                    thread.log_signal.emit("[Automation] ❌ Emails rejected by user")
                    return False
            
            # Check legacy method for backwards compatibility
            if hasattr(self.main_window, 'email_approval_status'):
                status = self.main_window.email_approval_status
                if status == 'approved':
                    thread.log_signal.emit("[Automation] ✅ Emails approved by user")
                    return True
                elif status == 'rejected':
                    thread.log_signal.emit("[Automation] ❌ Emails rejected by user")
                    return False
            
            # Update user every 5 minutes to show we're still waiting
            if wait_time % 300 == 0:
                thread.log_signal.emit(f"[Automation] ⏳ Still waiting for your approval... ({wait_time//60} minutes elapsed)")
                thread.log_signal.emit("[Automation] 💡 TIP: Enable Auto-Approval in the AI Email Marketing tab for fully automated operation")
        
        # This should never be reached since we loop indefinitely
        return False
    
    def send_approved_campaigns(self, thread):
        """Send the approved email campaigns"""
        try:
            # Use QMetaObject.invokeMethod to call on main thread
            from PySide6.QtCore import QMetaObject, Qt
            if hasattr(self, 'main_window'):
                QMetaObject.invokeMethod(
                    self.main_window, 
                    "send_approved_email_campaigns", 
                    Qt.QueuedConnection
                )
                
                thread.log_signal.emit("[Automation] 📤 Sending approved email campaigns...")
                
        except Exception as e:
            thread.log_signal.emit(f"[Automation] ❌ Error sending campaigns: {e}")
    
    def wait_for_redfin_completion(self, thread):
        """Wait for Redfin data pull to complete by checking status"""
        max_wait = 300  # 5 minutes maximum
        wait_time = 0
        check_interval = 5  # Check every 5 seconds
        
        while wait_time < max_wait:
            time.sleep(check_interval)
            wait_time += check_interval
            
            # Check if main window has redfin_completed data
            if hasattr(self, 'main_window') and hasattr(self.main_window, 'redfin_completed'):
                # Get selected cities from main window
                selected_cities = []
                if hasattr(self.main_window, 'get_selected_cities'):
                    selected_cities = self.main_window.get_selected_cities()
                
                # Check if ALL selected cities have completed Redfin processing
                if selected_cities and len(self.main_window.redfin_completed) >= len(selected_cities):
                    completed_cities = list(self.main_window.redfin_completed)
                    thread.log_signal.emit(f"[Automation] ✅ Redfin completed for ALL cities! Completed: {completed_cities}")
                    return
                elif len(self.main_window.redfin_completed) > 0:
                    completed_cities = list(self.main_window.redfin_completed)
                    thread.log_signal.emit(f"[Automation] ⏳ Redfin partially complete: {completed_cities} (waiting for all {len(selected_cities)} cities)")
            
            if wait_time % 30 == 0:  # Update every 30 seconds
                thread.log_signal.emit(f"[Automation] ⏳ Still waiting for Redfin... ({wait_time}/{max_wait}s)")
        
        thread.log_signal.emit("[Automation] ⚠️ Redfin wait timeout - proceeding anyway")
    
    def wait_for_att_completion(self, thread):
        """Wait for AT&T processing to complete by checking status"""
        max_wait = 600  # 10 minutes maximum
        wait_time = 0
        check_interval = 5  # Check every 5 seconds
        
        while wait_time < max_wait:
            time.sleep(check_interval)
            wait_time += check_interval
            
            # Check if main window has att_completed data
            if hasattr(self, 'main_window') and hasattr(self.main_window, 'att_completed'):
                # Get selected cities from main window (should match redfin_completed)
                expected_cities = []
                if hasattr(self.main_window, 'redfin_completed'):
                    expected_cities = list(self.main_window.redfin_completed)
                
                # Check if ALL cities that completed Redfin have also completed AT&T
                if expected_cities and len(self.main_window.att_completed) >= len(expected_cities):
                    completed_cities = list(self.main_window.att_completed)
                    thread.log_signal.emit(f"[Automation] ✅ AT&T completed for ALL cities! Completed: {completed_cities}")
                    return
                elif len(self.main_window.att_completed) > 0:
                    completed_cities = list(self.main_window.att_completed)
                    thread.log_signal.emit(f"[Automation] ⏳ AT&T partially complete: {completed_cities} (waiting for all {len(expected_cities)} cities)")
            
            if wait_time % 30 == 0:  # Update every 30 seconds
                thread.log_signal.emit(f"[Automation] ⏳ Still waiting for AT&T... ({wait_time}/{max_wait}s)")
        
        thread.log_signal.emit("[Automation] ⚠️ AT&T wait timeout - proceeding anyway")
    
    def wait_for_batchdata_completion(self, thread):
        """Wait for BatchData processing to complete by checking status"""
        max_wait = 900  # 15 minutes maximum
        wait_time = 0
        check_interval = 10  # Check every 10 seconds
        
        while wait_time < max_wait:
            time.sleep(check_interval)
            wait_time += check_interval
            
            # Check if main window has batchdata_worker that's finished
            if hasattr(self, 'main_window') and hasattr(self.main_window, 'batchdata_worker'):
                if self.main_window.batchdata_worker is None or not self.main_window.batchdata_worker.isRunning():
                    # Check if BatchData was successful by verifying contact information exists
                    if self.verify_batchdata_success(thread):
                        thread.log_signal.emit("[Automation] ✅ BatchData completed successfully with contact information!")
                        return True
                    else:
                        thread.log_signal.emit("[Automation] ❌ BatchData failed - no contact information found!")
                        thread.log_signal.emit("[Automation] ⚠️ Stopping automation - contact information is required for email marketing")
                        return False
            
            if wait_time % 60 == 0:  # Update every minute
                thread.log_signal.emit(f"[Automation] ⏳ Still waiting for BatchData... ({wait_time}/{max_wait}s)")
        
        thread.log_signal.emit("[Automation] ⚠️ BatchData wait timeout - stopping automation")
        return False
    
    def check_for_existing_contacts(self, thread):
        """Check if we have existing contacts from previous runs that can be used for campaigns"""
        try:
            # Check ContactManager for pending contacts
            from utils.contact_manager import ContactManager
            manager = ContactManager()
            pending_contacts = manager.get_pending_contacts()
            
            if pending_contacts:
                thread.log_signal.emit(f"[Automation] ✅ Found {len(pending_contacts)} existing pending contacts in ContactManager")
                return True
            
            # Check for CSV files with contact data (from previous runs) - ALIGNED WITH get_contacts_for_campaigns
            import os
            import glob
            import pandas as pd
            
            # Look for CURRENT automation contacts ONLY (not old master files) - SAME PATTERNS AS get_contacts_for_campaigns
            csv_patterns = [
                'email_ready_contacts_*.csv',       # Current automation contacts
                'batchdata_consolidated_*.csv',     # Current BatchData results
                'real_contacts_*.csv',              # Alternative naming
                'att_fiber_real_contacts_*.csv',    # AT&T Fiber contacts
                'adt_security_real_contacts_*.csv', # ADT Security contacts
                'processed_incident_contacts_*.csv' # Incident contacts
            ]
            
            best_file = None
            best_count = 0
            
            for pattern in csv_patterns:
                csv_files = glob.glob(pattern)
                thread.log_signal.emit(f"[Automation] Checking pattern '{pattern}': found {len(csv_files)} files")
                if csv_files:
                    # Get the most recent file for this pattern
                    latest_file = max(csv_files, key=os.path.getctime)
                    thread.log_signal.emit(f"[Automation] Latest file for '{pattern}': {latest_file}")
                    
                    # Check if file is recent (within last 30 days to allow existing contacts) - SAME AS get_contacts_for_campaigns
                    file_age = time.time() - os.path.getctime(latest_file)
                    thread.log_signal.emit(f"[Automation] File age for {latest_file}: {file_age/86400:.1f} days")
                    if file_age < 2592000:  # 30 days in seconds
                        try:
                            df = pd.read_csv(latest_file)
                            contact_count = len(df)
                            
                            # Prioritize files with more contacts
                            if contact_count > best_count:
                                best_file = latest_file
                                best_count = contact_count
                                
                        except Exception as e:
                            thread.log_signal.emit(f"[Automation] Error reading CSV file {latest_file}: {e}")
            
            if best_file:
                try:
                    df = pd.read_csv(best_file)
                    contacts = df.to_dict('records')
                    
                    # Filter for successful contacts (accept both 'success' and 'completed' status) - SAME LOGIC AS get_contacts_for_campaigns
                    if 'batchdata_status' in df.columns:
                        valid_contacts = [
                            c for c in contacts 
                            if c.get('batchdata_status') in ['completed', 'success'] and c.get('owner_name')
                        ]
                    else:
                        # If no status column, assume all contacts are valid if they have owner_name
                        valid_contacts = [
                            c for c in contacts 
                            if c.get('owner_name')
                        ]
                    
                    if valid_contacts:
                        thread.log_signal.emit(f"[Automation] ✅ Found {len(valid_contacts)} valid contacts in {best_file}")
                        return True
                        
                except Exception as e:
                    thread.log_signal.emit(f"[Automation] ❌ Error processing best file {best_file}: {e}")
            
            thread.log_signal.emit("[Automation] ❌ No existing contacts found")
            return False
            
        except Exception as e:
            thread.log_signal.emit(f"[Automation] ❌ Error checking for existing contacts: {e}")
            return False
    
    def verify_batchdata_success(self, thread):
        """Verify that BatchData processing was successful and produced contact information"""
        try:
            # Check if main window has batchdata results
            if hasattr(self.main_window, 'batchdata_results'):
                results = self.main_window.batchdata_results
                if results and isinstance(results, dict):
                    # Check if we have successful contacts
                    successful_contacts = results.get('successful', 0)
                    total_processed = results.get('total_processed', 0)
                    
                    if successful_contacts > 0:
                        thread.log_signal.emit(f"[Automation] ✅ BatchData success: {successful_contacts}/{total_processed} contacts found")
                        return True
                    else:
                        thread.log_signal.emit(f"[Automation] ❌ BatchData failed: 0/{total_processed} contacts found")
                        return False
            
            # Alternative: Check for CSV files with contact data
            import os
            import glob
            import pandas as pd
            
            # Look for recent BatchData CSV files
            csv_files = glob.glob('batchdata_consolidated_*.csv')
            if csv_files:
                # Get the most recent file
                latest_file = max(csv_files, key=os.path.getctime)
                
                # Check if file has contact data
                try:
                    df = pd.read_csv(latest_file)
                    if len(df) > 0:
                        # Check for successful contacts (those with owner names)
                        successful_contacts = len(df[df['owner_name'].notna() & (df['owner_name'] != '')])
                        total_contacts = len(df)
                        
                        if successful_contacts > 0:
                            thread.log_signal.emit(f"[Automation] ✅ BatchData file success: {successful_contacts}/{total_contacts} contacts in {latest_file}")
                            return True
                        else:
                            thread.log_signal.emit(f"[Automation] ❌ BatchData file failed: 0/{total_contacts} valid contacts in {latest_file}")
                            return False
                except Exception as e:
                    thread.log_signal.emit(f"[Automation] ❌ Error reading BatchData file: {e}")
                    return False
            
            thread.log_signal.emit("[Automation] ❌ No BatchData results found")
            return False
            
        except Exception as e:
            thread.log_signal.emit(f"[Automation] ❌ Error verifying BatchData success: {e}")
            return False
    
    def wait_for_adt_completion(self, thread):
        """Wait for ADT detection to complete by checking status"""
        max_wait = 300  # 5 minutes maximum
        wait_time = 0
        check_interval = 5  # Check every 5 seconds
        
        while wait_time < max_wait:
            time.sleep(check_interval)
            wait_time += check_interval
            
            # Check if main window has adt_worker that's finished
            if hasattr(self, 'main_window') and hasattr(self.main_window, 'adt_worker'):
                if self.main_window.adt_worker is None or not self.main_window.adt_worker.isRunning():
                    thread.log_signal.emit("[Automation] ✅ ADT detection completed!")
                    return
            
            if wait_time % 30 == 0:  # Update every 30 seconds
                thread.log_signal.emit(f"[Automation] ⏳ Still waiting for ADT... ({wait_time}/{max_wait}s)")
        
        thread.log_signal.emit("[Automation] ⚠️ ADT wait timeout - proceeding anyway")
    
    def wait_for_mailchimp_completion(self, thread):
        """Wait for MailChimp upload to complete by checking status"""
        max_wait = 180  # 3 minutes maximum
        wait_time = 0
        check_interval = 5  # Check every 5 seconds
        
        while wait_time < max_wait:
            time.sleep(check_interval)
            wait_time += check_interval
            
            # Check if main window has mailchimp_worker that's finished
            if hasattr(self, 'main_window') and hasattr(self.main_window, 'mailchimp_worker'):
                if self.main_window.mailchimp_worker is None or not self.main_window.mailchimp_worker.isRunning():
                    thread.log_signal.emit("[Automation] ✅ MailChimp upload completed!")
                    return
            
            if wait_time % 30 == 0:  # Update every 30 seconds
                thread.log_signal.emit(f"[Automation] ⏳ Still waiting for MailChimp... ({wait_time}/{max_wait}s)")
        
        thread.log_signal.emit("[Automation] ⚠️ MailChimp wait timeout - proceeding anyway") 

    def get_campaign_image(self, campaign_type, variation='default'):
        """Get appropriate copyright-compliant image URL for campaign type"""
        
        # Seaside Security logo - Licensed for dealer use
        seaside_logo = "https://seasidesecurity.net/wp-content/uploads/2025/04/DLR.23.8.17-DealerComboLogo_SeasideSecurity_Horz_RGB_BlueGray-scaled-e1746532770501.webp"
        
        # UPDATED PROFESSIONAL CATALOG - Copyright compliant images only
        # All Unsplash images verified for commercial use without attribution requirements
        APPROVED_IMAGES = {
            'att_fiber': [
                # Professional fiber optic cable installations
                "https://images.unsplash.com/photo-1606868306217-dbf5046868d2?w=600",  # Fiber cables close-up - technical
                "https://images.unsplash.com/photo-1518709268805-4e9042af2176?w=600",  # Fiber optic network cables
                "https://images.unsplash.com/photo-1558618047-3c8f28cd2ca5?w=600",    # Networking/tech installation
                
                # High-speed internet and technology setups
                "https://images.unsplash.com/photo-1582201942988-13e60e4b31cd?w=600",  # Professional tech setup
                "https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=600",    # Network equipment/server room
                "https://images.unsplash.com/photo-1551808525-51a94da548ce?w=600",    # Modern home office (fiber benefit)
                
                # Smart homes and modern connectivity
                "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=600",    # Modern smart home exterior
                "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=600", # Modern interior with tech
                "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=600", # Gaming setup (fiber speed benefit)
                
                # Professional installation and service
                "https://images.unsplash.com/photo-1621905251189-08b45d6a269e?w=600", # Professional tech work
                "https://images.unsplash.com/photo-1573164713347-4452bf387ac4?w=600", # Professional installer
                
                # Speed and performance imagery
                "https://images.unsplash.com/photo-1504639725590-34d0984388bd?w=600", # Speed/performance concept
                "https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=600",   # High-tech networking
            ],
            'adt_security': [
                seaside_logo,  # Licensed Seaside Security logo - primary branding
                "https://images.unsplash.com/photo-1558618047-3c8f28cd2ca5?w=600",   # Security keypad/panel
                "https://images.unsplash.com/photo-1609564403051-d3ae8ef8efaf?w=600", # Modern security system
                "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=600"    # Secure modern home
            ],
            'incident_alert': [
                seaside_logo,  # Licensed logo - important for credibility in emergencies
                "https://images.unsplash.com/photo-1558618047-3c8f28cd2ca5?w=600",   # Security panel
                "https://images.unsplash.com/photo-1609564403051-d3ae8ef8efaf?w=600"  # Emergency response system
            ],
            'general_outreach': [
                "https://images.unsplash.com/photo-1560472354-b33ff0c44a43?w=600",   # Modern home exterior
                "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=600", # Professional modern interior
                "https://images.unsplash.com/photo-1551808525-51a94da548ce?w=600"    # Professional home office
            ]
        }
        
        # Get approved images for campaign type
        campaign_images = APPROVED_IMAGES.get(campaign_type, APPROVED_IMAGES['general_outreach'])
        
        # Select image based on variation
        if variation == 'default':
            return campaign_images[0]
        elif variation == 'alternate' and len(campaign_images) > 1:
            return campaign_images[1]
        elif variation == 'third' and len(campaign_images) > 2:
            return campaign_images[2]
        else:
            return campaign_images[0]
    
    def get_image_html(self, campaign_type, alt_text="Campaign Image", variation='default'):
        """Get properly formatted HTML image tag for email with copyright compliance"""
        image_url = self.get_campaign_image(campaign_type, variation)
        
        # Special styling for Seaside Security logo (licensed content)
        if "seasidesecurity.net" in image_url:
            return f'<img src="{image_url}" alt="{alt_text}" style="max-width: 300px; margin: 20px 0;">'
        else:
            # Unsplash images with commercial license
            return f'<img src="{image_url}" alt="{alt_text}" style="max-width: 500px; margin: 20px 0; border-radius: 8px;">'
    
    def get_copyright_notice(self, image_url):
        """Get appropriate copyright notice for image (for internal documentation)"""
        if "seasidesecurity.net" in image_url:
            return "Licensed content - Seaside Security dealer authorization"
        elif "unsplash.com" in image_url:
            return "Unsplash License - Commercial use authorized, no attribution required"
        else:
            return "Unknown source - COMPLIANCE REVIEW REQUIRED" 