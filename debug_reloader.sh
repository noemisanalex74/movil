#!/bin/bash

echo "--- Starting dashboard to trigger reloader issue ---"
# Run the main startup script in the background
/data/data/com.termux/files/home/.shortcuts/start_agp_dashboard.sh &

# Wait for the server to start and then restart
echo "--- Waiting 5 seconds for the issue to occur ---"
sleep 5

echo "--- Killing server process to stop the loop ---"
pkill -f 'python app.py'

echo "--- Finding the 10 most recently modified files in agp-dashboard-web ---"
cd /data/data/com.termux/files/home/agp-dashboard-web
# The find command will show which file was modified last
find . -type f -printf '%T@ %p\n' | sort -n | tail -n 10
