## Calendar utilities and Notification for The Collaborative

## Configuration
The gspread library gets its credentials from a service_account credentials file.  This file is found in: 
~/.config/gspread/service_account.json

If you are running it from launchd - it needs to be in the root account's home directory: 
/var/root/.config/service_account.json

## Running
To run this use a .plist

### To schedule for a specific time per day: 
```
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>18</integer>
        <key>Minute</key>
        <integer>5</integer>
    </dict>
```

### To schedule for intervals (every 20 seconds)
```
   <key>StartInterval</key>
    <integer>20</integer>
```
---


When creating a new plist, change the permissions: 
```
sudo chown root:wheel ~/Library/LaunchAgents/com.collab.notify.plist
```

### To install a plist that will run a scheduled job: 
```
sudo launchctl load ~/Library/LaunchAgents/com.collab.notify.plist

sudo launchctl unload ~/Library/LaunchAgents/com.collab.notify.plist
```

### TODO: 

* Save whole month before performing aggregate operations (such as assign_tango).  Restore previous state
* add 30 minute granularity
* 