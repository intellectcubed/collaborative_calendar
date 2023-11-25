#!/bin/bash

export GOOGLE_APPLICATION_CREDENTIALS='/Users/georgenowakowski/Downloads'

cd /Users/georgenowakowski/Projects/EMSCollaborative/collaborative_calendar
source /Users/georgenowakowski/Projects/EMSCollaborative/collaborative_calendar/venv/bin/activate
python /Users/georgenowakowski/Projects/EMSCollaborative/collaborative_calendar/crew_notifier.py --environment devo --to_test_email

