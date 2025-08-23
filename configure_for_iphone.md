# Configure MobileSalesApp for iPhone Deployment

## Step 3: Configure Project Settings

### 1. Select the Project
- **Click on "MobileSalesApp"** in the project navigator (left sidebar)
- **Click on "MobileSalesApp"** under TARGETS (not the project, but the target)

### 2. Configure Signing
- **Go to "Signing & Capabilities" tab**
- **Check "Automatically manage signing"**
- **Team**: Select your Apple ID from the dropdown
- **Bundle Identifier**: Change to something unique like:
  - `com.yourname.mobilesalesapp`
  - `com.seasidesecurity.mobilesalesapp`
  - `com.yourcompany.mobilesalesapp`

### 3. Configure Deployment Info
- **Go to "General" tab**
- **Display Name**: "Mobile Sales App" (or whatever you want)
- **Deployment Info**:
  - **iOS Deployment Target**: 17.0 (or your iPhone's iOS version)
  - **Devices**: iPhone (uncheck iPad if you only want iPhone)

### 4. Select Your iPhone
- **At the top of Xcode**, you'll see a device selector
- **Click the dropdown** and select your iPhone
- **If your iPhone doesn't appear**:
  - Make sure it's connected via USB
  - Check that you've trusted the computer on your iPhone
  - Try disconnecting and reconnecting

### 5. Build and Run
- **Click the Play button** (▶️) or press **Cmd+R**
- **Xcode will build** and install the app on your iPhone
- **On your iPhone**, you may need to:
  - Go to **Settings → General → VPN & Device Management**
  - Find your Apple ID and tap **"Trust"**

## Troubleshooting

### "No provisioning profiles found"
- Make sure you're signed in with your Apple ID in Xcode
- Try refreshing the signing certificates

### "Device not found"
- Check USB connection
- Make sure iPhone is unlocked
- Try a different USB cable

### "App won't install"
- Check iPhone storage space
- Make sure you've trusted the developer certificate

## Success!
Once installed, you'll have:
✅ Full working app with all features
✅ Real maps integration
✅ Phone call functionality
✅ Big Beautiful Program sync
✅ Region assignment system
✅ Dark mode

The app will work much better on your actual iPhone than in the simulator!
