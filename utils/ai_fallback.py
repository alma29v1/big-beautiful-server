def simple_ai_chat(query: str) -> str:
    """Simple AI chat fallback when xAI is not working"""
    
    # Simple response patterns
    responses = {
        "hello": "Hello! I'm here to help with your email marketing. How can I assist you today?",
        "help": "I can help you with email marketing campaigns, AT&T Fiber promotions, ADT Security offers, and general outreach. What would you like to work on?",
        "campaign": "Great! Let's create an email campaign. What type of campaign are you looking to create - AT&T Fiber, ADT Security, or general outreach?",
        "fiber": "Perfect! For AT&T Fiber campaigns, we focus on high-speed internet benefits, competitive pricing, and easy installation. What specific aspect would you like to highlight?",
        "security": "Excellent! For ADT Security campaigns, we emphasize 24/7 monitoring, smart home integration, and family protection. What would you like to focus on?",
        "new home": "Excellent idea! New homeowners are perfect for AT&T Fiber campaigns. Let me create a 'Welcome to Your New Home' campaign focused on getting them connected with the fastest internet available.",
        "new homeowner": "Perfect! New homeowners need internet setup. Let me generate a professional campaign welcoming them to their new home and offering AT&T Fiber installation.",
        "welcome": "Great approach! A 'Welcome to Your New Home' campaign is much more effective than generic upgrade messaging. Let me create that for you.",
        "hook up": "I understand! Let me create a professional 'Welcome to Your New Home' campaign that focuses on getting new homeowners connected with AT&T Fiber internet service.",
        "test": "I'm working! This is a test response. The AI service is functioning properly.",
        "automation": "I can help you run the automation! The system is ready to process AT&T Fiber leads and generate campaigns. Would you like me to start the automation now?",
        "run automation": "Starting the automation now! This will process your AT&T Fiber leads and generate new homeowner-focused campaigns.",
        "start automation": "Perfect! I'm starting the automation workflow. This will include lead processing, campaign generation, and email marketing setup.",
        "your marketing strategies": "I'd love to discuss your marketing strategies! We can focus on new homeowner campaigns, AT&T Fiber promotions, ADT Security offers, or general outreach. What would you like to explore?",
        "can you run the automation": "Absolutely! I'm starting the automation now. This will process your leads and generate professional campaigns focused on new homeowners and AT&T Fiber availability."
    }
    
    # Check for specific patterns in the query
    query_lower = query.lower()
    
    # New homeowner focused responses
    if any(phrase in query_lower for phrase in ["new home", "new homeowner", "moving", "just moved", "welcome"]):
        return """Perfect! I'll create a new homeowner-focused AT&T Fiber campaign. Here's what I'll generate:

**Campaign Focus: Welcome to Your New Home**
- Subject Lines: "Welcome to Your New Home - Get Connected with AT&T Fiber"
- Email Content: Professional welcome message emphasizing internet setup for new homeowners
- Call-to-Action: "Schedule Your New Home Internet Installation"

This approach is much more effective than generic upgrade messaging since new homeowners actually need internet service!"""

    # AT&T Fiber specific responses
    if any(phrase in query_lower for phrase in ["fiber", "internet", "at&t", "att"]):
        if any(phrase in query_lower for phrase in ["upgrade", "better", "faster"]):
            return """I understand! Instead of generic upgrade messaging, let's focus on new homeowners who actually need internet service. This is a much better angle because:

1. **New homeowners need internet** - they don't have service yet
2. **Perfect timing** - they're setting up their new home
3. **Higher conversion** - they're actively looking for providers
4. **Professional approach** - "Welcome to your new home, let us help you get connected"

Would you like me to generate a new homeowner-focused campaign now?"""
        else:
            return """Great! For AT&T Fiber campaigns, I recommend focusing on new homeowners because:
- They actually need internet service (not just an upgrade)
- Perfect timing for installation
- Higher conversion rates
- More professional approach

What specific aspect would you like me to highlight in the campaign?"""

    # Check for exact matches first
    for key, response in responses.items():
        if key in query_lower:
            return response
    
    # Check for partial matches
    for key, response in responses.items():
        if any(word in query_lower for word in key.split()):
            return response
    
    # Default response for unrecognized queries
    return "I understand! I'm here to help with your email marketing campaigns. Would you like me to generate a new homeowner-focused AT&T Fiber campaign, or is there something else I can assist you with?"
