# Adding RegionAssignmentView to Xcode Project

## Quick Fix for Build Error

The build is failing because `RegionAssignmentView.swift` is not added to the Xcode project. Here's how to fix it:

### Method 1: Drag and Drop (Easiest)
1. **In Xcode**, make sure the project navigator is visible (left sidebar)
2. **Right-click** on the "MobileSalesApp" folder (yellow folder icon)
3. **Select "Add Files to MobileSalesApp"**
4. **Navigate to**: `/Volumes/LaCie/MobileSalesProject/MobileSalesApp/RegionAssignmentView.swift`
5. **Select the file** and click "Add"
6. **Make sure** "Add to target: MobileSalesApp" is checked
7. **Click "Add"**

### Method 2: Create New File
1. **Right-click** on "MobileSalesApp" folder in Xcode
2. **Select "New File..."**
3. **Choose "Swift File"**
4. **Name it**: `RegionAssignmentView`
5. **Copy and paste** the contents from the existing file

### After Adding the File:
1. **Clean the build** (Product → Clean Build Folder)
2. **Build again** (Cmd+B)
3. **The error should be gone!**

## Next Steps for iPhone Deployment:
1. **Select your iPhone** in the device dropdown (top of Xcode)
2. **Configure signing** (see next steps)
3. **Build and run** (Cmd+R)

The RegionAssignmentView adds the territory management feature where you can assign cities to salespeople!
