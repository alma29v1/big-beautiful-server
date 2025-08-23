# 🔒 Secure Replit Cloud Server Setup Guide

## 🚨 **IMPORTANT: API Key Security**

Your previous API keys were exposed when the repository went public. This new version is completely secure with NO hardcoded keys.

## 📋 **What We've Fixed**

✅ **Removed All Hardcoded API Keys**
✅ **Created Secure Server Code**
✅ **Generated New API Key**
✅ **Updated iPhone App**
✅ **Created Secure Test Script**

## 🔑 **New API Key**

**⚠️ IMPORTANT: Generate your own API key!**

```bash
# Generate a new secure API key
python3 -c "import secrets; print('New API Key:', secrets.token_urlsafe(32))"
```

**⚠️ IMPORTANT: Keep this key secret! Never commit it to public repositories.**

## 🌐 **Step-by-Step Replit Setup**

### **Step 1: Create New Replit Project**
1. Go to [replit.com](https://replit.com)
2. Click **"Create Repl"**
3. Choose **"Python"** as language
4. Name it: `big-beautiful-api-server-secure`

### **Step 2: Upload the Secure Server Code**
1. Copy the contents of `replit_api_server_secure.py`
2. Paste it into the main `.py` file in your Repl
3. Save the file

### **Step 3: Set Environment Variables (CRITICAL)**
1. Click **"Tools"** → **"Secrets"**
2. Add these variables:

```
Key: MOBILE_APP_API_KEY
   Value: YOUR_GENERATED_API_KEY_HERE
```

```
Key: GOOGLE_API_KEY
Value: your_new_google_api_key_here (optional)
```

### **Step 4: Install Dependencies**
1. Create a `requirements.txt` file with:
```
Flask==2.3.3
Flask-CORS==4.0.0
requests==2.31.0
python-dotenv==1.0.0
```

### **Step 5: Run the Server**
1. Click the **"Run"** button
2. Your server URL will be: `https://your-repl-name.your-username.repl.co`

## 📱 **iPhone App Configuration**

Your iPhone app is already updated with the new API key and will connect to:
- **Primary**: Your new Replit server (HTTPS)
- **Fallback 1**: Local network server
- **Fallback 2**: External server
- **Fallback 3**: Localhost

## 🧪 **Testing the Connection**

### **Option 1: Use the Secure Test Script**
```bash
# Set your API key as environment variable
export MOBILE_APP_API_KEY="YOUR_GENERATED_API_KEY_HERE"

# Run the test
python test_replit_connection_secure.py
```

### **Option 2: Test with curl**
```bash
# Health check
curl https://your-repl-name.your-username.repl.co/api/health

# Test contacts (with new API key)
curl -H "X-API-Key: YOUR_GENERATED_API_KEY_HERE" \
     https://your-repl-name.your-username.repl.co/api/contacts
```

## 🔧 **API Endpoints Available**

- `GET /api/health` - Health check (shows API key status)
- `GET /api/contacts` - Get all contacts
- `GET /api/contacts/<id>` - Get specific contact
- `POST /api/contacts` - Create new contact
- `POST /api/geocode` - Geocode address (requires Google API key)
- `POST /api/att-fiber-check` - Check AT&T Fiber
- `GET /api/analytics` - Get analytics
- `POST /api/sync` - Sync data
- `GET /api/rolling-sales` - Get rolling weekly sales
- `GET /api/rolling-sales/export` - Export for AI email

## 🛡️ **Security Features**

✅ **No Hardcoded Keys**: All keys from environment variables
✅ **API Key Validation**: Server won't start without API key
✅ **HTTPS Only**: Secure connections
✅ **Input Validation**: All data validated
✅ **Error Handling**: Proper error responses

## 🚨 **Troubleshooting**

### **Server Won't Start**
- **Error**: "MOBILE_APP_API_KEY environment variable is required!"
- **Solution**: Set the API key in Replit Secrets

### **Connection Failed**
- Verify the Replit URL is correct
- Check if the server is running
- Test with health check endpoint

### **API Key Issues**
- Ensure `X-API-Key` header is included
- Verify the key matches your generated API key

### **Google API Issues**
- If geocoding doesn't work, set `GOOGLE_API_KEY` in Secrets
- Or leave it unset - geocoding will be disabled

## 📊 **Database Storage**

- **Location**: `/tmp/big_beautiful_api.db` on Replit
- **Persistence**: Data persists between restarts
- **Backup**: Consider regular exports for important data

## 🎯 **Benefits of This Secure Version**

✅ **No Exposed Keys**: Completely safe for public repositories
✅ **Environment Variables**: Keys stored securely
✅ **Validation**: Server validates required keys on startup
✅ **Flexible**: Easy to change keys without code changes
✅ **Production Ready**: Secure by design

## 📞 **Support**

If you encounter issues:
1. Check Replit logs for error messages
2. Verify environment variables are set correctly
3. Test with the secure test script
4. Check the health endpoint for configuration status

## 🎉 **Success Indicators**

You'll know it's working when:
- ✅ Replit server shows "Running" status
- ✅ Health check returns 200 OK with API key status
- ✅ iPhone app connects successfully
- ✅ Sync button works in the app
- ✅ Data loads in all tabs

## 🔄 **Updating the Server**

To update your server:
1. Make changes to the code
2. Save the file
3. Replit will automatically restart the server
4. Test with the health endpoint

---

**Your secure cloud server is ready! Follow the steps above to deploy.** 🔒🚀
