## Calendar utilities and Notification for The Collaborative

## How to add a new package?  (Standard Python stuff, but here for convenience)
- Find which version you want
- update ```requirements.txt```
- Install: 
```
pip install -r requirements.txt
```

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


---
## New "test" environment is available.
When starting collab_i.py, you can specify the test environment.  This will have the effect of not connecting to a Google Calendar, but instead using the **ersats_google_calendar_mgr.py** manager.  This allows testing without Google or even the internet.  The file: test/test_cases/expected_results/May_2024.txt is used to drive the calendar data (thus not needing to connect to Google calendar).  If the results of the modify operation differ from the original day, you will have the option to update the day with the values so that when you run collab_i again for that day, your modified calendar will be used.

You may use this for capturing test cases as well (see below).

# Testing
A test harness was created that will enable you to run collab_i normally, pointing to any environment.  As you provide commands interactively, the calls are captured to "test case capture" files consisting of the decorated methods.  3 files are saved: _args, _kwargs and _retval.dill.  These files contain the parameters.  

## To capture test cases (creating new scenarios):
```
python collab_i.py --environment test --build_tests
```

- Note: test or devo environments are recommended, but prod will work too.

## To run through test cases
```
python shift_testing_runner.py --test_id Test_1717120966
```

You can leave off the --test-id parameter and all tests will be run.