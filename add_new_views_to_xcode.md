# 🔧 Add New Views to Xcode Project

## ❌ **Build Error Found:**
```
Cannot find 'TerritoryDrawingView' in scope
Cannot find 'LeadMarketplaceView' in scope
```

## ✅ **Quick Fix - Add Files to Xcode:**

### **Step 1: Add TerritoryDrawingView.swift**
1. In Xcode, **right-click** on the `MobileSalesApp` folder
2. Select **"Add Files to 'MobileSalesApp'"**
3. Navigate to: `/Volumes/LaCie/MobileSalesProject/MobileSalesApp/`
4. Select **`TerritoryDrawingView.swift`**
5. Click **"Add"**

### **Step 2: Add LeadMarketplaceView.swift**
1. In Xcode, **right-click** on the `MobileSalesApp` folder
2. Select **"Add Files to 'MobileSalesApp'"**
3. Navigate to: `/Volumes/LaCie/MobileSalesProject/MobileSalesApp/`
4. Select **`LeadMarketplaceView.swift`**
5. Click **"Add"**

### **Step 3: Build & Deploy**
1. **Clean Build Folder**: Cmd+Shift+K
2. **Build**: Cmd+B
3. **Deploy to iPhone**: Click Play ▶️

## 🎯 **Alternative: Automatic Script**

Run this command in Terminal:
```bash
cd /Volumes/LaCie/MobileSalesProject
./build_and_deploy.sh
```

## ✅ **Expected Result:**
- ✅ Build successful
- ✅ 7 tabs for Manager (including Territories & Marketplace)
- ✅ 4 tabs for Employee
- ✅ All features working

## 🚀 **Files Ready to Add:**
- ✅ `TerritoryDrawingView.swift` - Map territory drawing
- ✅ `LeadMarketplaceView.swift` - Lead buying/selling

**Add these 2 files to Xcode and you're ready to deploy!** 📱
