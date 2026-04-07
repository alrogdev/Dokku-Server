#!/bin/bash
# scripts/cron/update-geoip.sh
# Update CrowdSec GeoIP database weekly

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../lib/telegram.sh"

LOG_FILE="/var/log/crowdsec-geoip-update.log"

echo "[$(date)] Starting GeoIP database update..." >> "$LOG_FILE"

# Update CrowdSec hub (includes GeoIP databases)
if cscli hub update >> "$LOG_FILE" 2>&1; then
    echo "[$(date)] Hub updated successfully" >> "$LOG_FILE"
    
    # Upgrade collections to get latest GeoIP data
    if cscli collections upgrade -a >> "$LOG_FILE" 2>&1; then
        echo "[$(date)] Collections upgraded successfully" >> "$LOG_FILE"
        
        # Reload CrowdSec to apply updates
        if systemctl reload crowdsec >> "$LOG_FILE" 2>&1; then
            MESSAGE="🌍 <b>GeoIP Update Successful</b>

✅ CrowdSec hub updated
✅ Collections upgraded
✅ Service reloaded

<i>Next update: $(date -d '+7 days' '+%Y-%m-%d')</i>"
            
            send_telegram_message "$MESSAGE"
            echo "[$(date)] Update completed successfully" >> "$LOG_FILE"
        else
            echo "[$(date)] Failed to reload CrowdSec" >> "$LOG_FILE"
            send_telegram_alert "GeoIP Update Warning" "Hub updated but failed to reload CrowdSec" "⚠️"
        fi
    else
        echo "[$(date)] Failed to upgrade collections" >> "$LOG_FILE"
        send_telegram_alert "GeoIP Update Failed" "Failed to upgrade CrowdSec collections" "❌"
        exit 1
    fi
else
    echo "[$(date)] Failed to update hub" >> "$LOG_FILE"
    send_telegram_alert "GeoIP Update Failed" "Failed to update CrowdSec hub" "❌"
    exit 1
fi
