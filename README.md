# Big Beautiful Server - Secure API Server

A secure Flask API server for the iPhone mobile sales app, designed to run on Replit.com.

## 🔒 **Security First**

This repository is **completely safe to make public** because:
- ✅ **No hardcoded API keys** anywhere in the code
- ✅ **All keys use environment variables**
- ✅ **Server validates keys on startup**
- ✅ **Secure by design**

## 🚀 **Quick Start**

### **1. Generate Your API Key**
```bash
python3 -c "import secrets; print('New API Key:', secrets.token_urlsafe(32))"
```

### **2. Deploy to Replit**
1. Go to [replit.com](https://replit.com)
2. Click "Create Repl"
3. Choose "Import from GitHub"
4. Select this repository
5. Set environment variable in Secrets:
   - Key: `MOBILE_APP_API_KEY`
   - Value: `YOUR_GENERATED_API_KEY_HERE`

### **3. Update iPhone App**
Replace `YOUR_API_KEY_HERE` in `MobileSalesApp/BigBeautifulAPIClient.swift` with your generated API key.

## 📱 **API Endpoints**

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

## 🛡️ **Security Features**

- **No Hardcoded Keys**: All keys from environment variables
- **API Key Validation**: Server won't start without API key
- **HTTPS Only**: Secure connections
- **Input Validation**: All data validated
- **Error Handling**: Proper security responses

## 📋 **Files**

- `replit_api_server_secure.py` - Main server code
- `test_replit_connection_secure.py` - Test script
- `requirements.txt` - Python dependencies
- `FINAL_DEPLOYMENT_GUIDE.md` - Complete setup guide
- `SECURE_REPLIT_SETUP_GUIDE.md` - Detailed instructions
- `API_KEY_REFERENCE.md` - API key setup guide

## 🔧 **Development**

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python replit_api_server_secure.py
```

## 📞 **Support**

See the deployment guides for detailed setup instructions and troubleshooting.

---

**This repository is safe to make public - no secrets are exposed!** 🔒
