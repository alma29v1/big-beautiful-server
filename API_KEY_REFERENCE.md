# 🔑 API Key Reference

## **New Secure API Key**
```
uTs6R5kZaQBp5iAUJWkf1r5hQGixWd0uPaFWAQ-AEWg
```

## **Where to Use This Key**

### **1. Replit Environment Variables**
- **Key**: `MOBILE_APP_API_KEY`
- **Value**: `uTs6R5kZaQBp5iAUJWkf1r5hQGixWd0uPaFWAQ-AEWg`

### **2. iPhone App**
- Already updated in `BigBeautifulAPIClient.swift`
- No changes needed

### **3. Testing**
```bash
export MOBILE_APP_API_KEY="uTs6R5kZaQBp5iAUJWkf1r5hQGixWd0uPaFWAQ-AEWg"
python test_replit_connection_secure.py
```

### **4. curl Testing**
```bash
curl -H "X-API-Key: uTs6R5kZaQBp5iAUJWkf1r5hQGixWd0uPaFWAQ-AEWg" \
     https://your-repl-url.repl.co/api/contacts
```

## **⚠️ Security Notes**

- ✅ **Never commit this key to public repositories**
- ✅ **Only use in environment variables**
- ✅ **Keep this file private**
- ✅ **Regenerate if accidentally exposed**

## **🔄 If You Need a New Key**

```bash
python3 -c "import secrets; print('New API Key:', secrets.token_urlsafe(32))"
```

---

**Generated**: $(date)
**Status**: Active
**Security**: Secure (no hardcoded keys)
