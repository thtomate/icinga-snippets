#!/bin/bash

TIME_INTERVAL="5days"

JOURNALCTL_CMD="journalctl --no-hostname -xeu puppet --grep zone.*removed --since -$TIME_INTERVAL --no-pager | sed '/^-- No entries --$/d'"
RETURN_VAL=$(eval "$JOURNALCTL_CMD")

LINE_COUNT=$(echo "$RETURN_VAL" | sed '/^$/d' | wc -l)

if [ "$LINE_COUNT" -eq "0" ]; then
    echo "OK - No hosts deleted from monitoring in last $TIME_INTERVAL."
    exit 0
else
    echo "WARNING - $LINE_COUNT Log: $RETURN_VAL"
    exit 1
fi
