# 🚀 Replit Cloud Server Setup Guide

## 📋 **What We've Accomplished**

✅ **Created GitHub Repository**: `alma29v1/big-beautiful-api-server`
✅ **Uploaded API Server Code**: Complete Flask API for mobile app
✅ **Updated iPhone App**: Configured to connect to Replit server
✅ **Added HTTPS Support**: Proper SSL/TLS configuration
✅ **Created Test Script**: To verify server functionality

## 🌐 **Next Steps: Deploy to Replit**

### **Step 1: Go to Replit.com**
1. Visit [replit.com](https://replit.com)
2. Sign in or create an account

### **Step 2: Import from GitHub**
1. Click **"Create Repl"**
2. Choose **"Import from GitHub"**
3. Select: `alma29v1/big-beautiful-api-server`
4. Choose **"Python"** as language
5. Click **"Import from GitHub"**

### **Step 3: Configure Environment Variables**
1. Click **"Tools"** → **"Secrets"**
2. Add these variables:
   ```
   Key: MOBILE_APP_API_KEY
   Value: h_opOMev4WtqADSPO59qVgEhvrvxt7Q0D96lU94kpl8

   Key: GOOGLE_API_KEY
   Value: your_google_api_key_here (optional)
   ```

### **Step 4: Run the Server**
1. Click the **"Run"** button
2. Your server URL will be:
   ```
   https://big-beautiful-api-server.alma29v1.repl.co
   ```

## 📱 **iPhone App Configuration**

Your iPhone app is now configured to:
- ✅ **Primary**: Connect to Replit cloud server (HTTPS)
- ✅ **Fallback 1**: Local network server (192.168.84.130:5001)
- ✅ **Fallback 2**: External server (65.190.137.27:5001)
- ✅ **Fallback 3**: Localhost (127.0.0.1:5001)

## 🧪 **Testing the Connection**

### **Option 1: Use the Test Script**
```bash
python test_replit_connection.py
```

### **Option 2: Test with curl**
```bash
# Health check
curl https://big-beautiful-api-server.alma29v1.repl.co/api/health

# Test contacts (with API key)
curl -H "X-API-Key: h_opOMev4WtqADSPO59qVgEhvrvxt7Q0D96lU94kpl8" \
     https://big-beautiful-api-server.alma29v1.repl.co/api/contacts
```

## 🔧 **API Endpoints Available**

- `GET /api/health` - Health check
- `GET /api/contacts` - Get all contacts
- `GET /api/contacts/<id>` - Get specific contact
- `POST /api/contacts` - Create new contact
- `POST /api/geocode` - Geocode address
- `POST /api/att-fiber-check` - Check AT&T Fiber
- `GET /api/analytics` - Get analytics
- `POST /api/sync` - Sync data
- `GET /api/rolling-sales` - Get rolling weekly sales
- `GET /api/rolling-sales/export` - Export for AI email

## 🎯 **Benefits of Replit Cloud**

✅ **Always Online**: No need to keep your computer running
✅ **Public HTTPS**: Works from anywhere, no ATS issues
✅ **Free Hosting**: No additional costs
✅ **Easy Updates**: Just push to GitHub
✅ **Automatic Scaling**: Handles multiple users
✅ **Built-in Database**: SQLite storage

## 📊 **Database Storage**

- **Location**: `/tmp/big_beautiful_api.db` on Replit
- **Persistence**: Data persists between restarts
- **Backup**: Consider regular exports for important data

## 🔒 **Security Features**

- **API Key Authentication**: All endpoints protected
- **HTTPS Only**: Secure connections
- **CORS Enabled**: Cross-origin requests allowed
- **Input Validation**: All data validated

## 🚨 **Troubleshooting**

### **Server Won't Start**
- Check Replit logs for errors
- Verify environment variables are set
- Ensure all dependencies are installed

### **Connection Failed**
- Verify the Replit URL is correct
- Check if the server is running
- Test with the health check endpoint

### **API Key Issues**
- Ensure `X-API-Key` header is included
- Verify the key matches: `h_opOMev4WtqADSPO59qVgEhvrvxt7Q0D96lU94kpl8`

## 📞 **Support**

If you encounter issues:
1. Check Replit logs
2. Run the test script
3. Verify GitHub repository is up to date
4. Check environment variables

## 🎉 **Success Indicators**

You'll know it's working when:
- ✅ Replit server shows "Running" status
- ✅ Health check returns 200 OK
- ✅ iPhone app connects successfully
- ✅ Sync button works in the app
- ✅ Data loads in all tabs

---

**Your cloud server is ready! Just follow the Replit setup steps above.** 🚀
