# Big Beautiful Program API Server

Cloud-hosted API server for the iPhone mobile sales app, designed to run on Replit.com.

## 🚀 Features

- **Contacts Management**: CRUD operations for sales contacts
- **AT&T Fiber Checking**: Check fiber availability for addresses
- **Geocoding**: Convert addresses to coordinates using Google Maps API
- **Analytics**: Sales analytics and reporting
- **Rolling Sales Data**: Weekly sales tracking
- **Secure API**: API key authentication

## 📱 API Endpoints

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

## 🔑 Authentication

All endpoints (except health check) require the `X-API-Key` header:
```
X-API-Key: h_opOMev4WtqADSPO59qVgEhvrvxt7Q0D96lU94kpl8
```

## 🌐 Deployment

This server is designed to run on Replit.com for cloud hosting.

### Environment Variables

Set these in Replit's Secrets tab:
- `MOBILE_APP_API_KEY`: Your API key (default: h_opOMev4WtqADSPO59qVgEhvrvxt7Q0D96lU94kpl8)
- `GOOGLE_API_KEY`: Google Maps API key for geocoding

## 📊 Database

Uses SQLite database stored in `/tmp/big_beautiful_api.db` on Replit.

## 🔧 Setup Instructions

1. Fork this repository to your GitHub account
2. Go to [replit.com](https://replit.com)
3. Click "Create Repl"
4. Choose "Import from GitHub"
5. Select your forked repository
6. Set environment variables in Replit Secrets
7. Run the server

## 📱 iPhone App Integration

Your iPhone app will connect to the Replit URL:
```
https://your-repl-name.your-username.repl.co/api
```

## 🛠️ Development

To run locally:
```bash
pip install -r requirements.txt
python replit_api_server.py
```

## 📄 License

Private use only - Mobile Sales App Integration 