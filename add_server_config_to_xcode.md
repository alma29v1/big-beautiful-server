# Add ServerConfigurationView.swift to Xcode Project

## Steps to Add the File:

1. **Open Xcode** with the MobileSalesApp project

2. **Right-click on the "MobileSalesApp" folder** in the left navigator panel

3. **Select "Add Files to 'MobileSalesApp'"**

4. **Navigate to and select** `/Volumes/LaCie/MobileSalesProject/MobileSalesApp/ServerConfigurationView.swift`

5. **Make sure the checkbox is checked** for your target (MobileSalesApp)

6. **Click "Add"**

## What this does:
- Adds the new ServerConfigurationView.swift file to your Xcode project
- Allows you to configure remote server connections
- Provides a UI to change from localhost to your computer's IP address
- Includes connection testing functionality

## After adding the file:
- Build the project to make sure there are no errors
- The "Server Configuration" button will work in the Big Beautiful tab
- You can change the server address from localhost to your computer's IP

## Finding Your Computer's IP Address:
- **Mac**: System Preferences > Network > Select your connection > IP address shown
- **Windows**: Open Command Prompt > type `ipconfig` > look for IPv4 Address
- **Linux**: Open Terminal > type `ip addr show` or `ifconfig`

## Example Setup:
- Change server host from "localhost" to your IP (e.g., "192.168.1.100")
- Keep port as "5001"
- Test connection to make sure it works
- Save settings
