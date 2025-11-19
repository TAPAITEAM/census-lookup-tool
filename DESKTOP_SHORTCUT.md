# Creating a Desktop Shortcut (Optional)

## Windows

1. Right-click on your Desktop
2. Select **New → Shortcut**
3. For the location, enter:
   ```
   cmd /c "cd /d C:\path\to\LMIUpdate && START_HERE.bat"
   ```
   (Replace `C:\path\to\LMIUpdate` with the actual folder path)
4. Click **Next**
5. Name it: "Census Lookup Tool"
6. Click **Finish**

Now you can double-click the shortcut from your desktop!

---

## Mac

1. Open **Automator** (search in Spotlight)
2. Select **Application**
3. Add action: **Run Shell Script**
4. Enter:
   ```bash
   cd /path/to/LMIUpdate
   ./START_HERE.sh
   ```
   (Replace `/path/to/LMIUpdate` with the actual folder path)
5. Save as "Census Lookup Tool" to your Desktop

---

## Linux

Create a `.desktop` file on your desktop:

1. Create a file: `~/Desktop/census-lookup.desktop`
2. Add this content:
   ```ini
   [Desktop Entry]
   Type=Application
   Name=Census Lookup Tool
   Exec=/bin/bash /path/to/LMIUpdate/START_HERE.sh
   Icon=utilities-terminal
   Terminal=true
   ```
   (Replace `/path/to/LMIUpdate` with the actual folder path)
3. Make it executable:
   ```bash
   chmod +x ~/Desktop/census-lookup.desktop
   ```

---

## Easier Alternative

Instead of creating a shortcut, you can:
1. Open File Explorer / Finder
2. Navigate to the LMIUpdate folder
3. Bookmark or add to favorites
4. Double-click `START_HERE.bat` or `START_HERE.sh` each time
