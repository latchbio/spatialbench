#!/bin/bash
set -e

echo "=========================================="
echo "Cleaning up orphaned multiprocessing workers"
echo "=========================================="
echo ""

ORPHANED_COUNT=$(ps aux | grep 'from multiprocessing' | grep -v grep | wc -l | tr -d ' ')

if [ "$ORPHANED_COUNT" -eq 0 ]; then
    echo "No orphaned processes found."
    exit 0
fi

echo "Found $ORPHANED_COUNT orphaned multiprocessing worker processes"
echo ""

read -p "Kill all orphaned processes? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo "Killing orphaned processes..."
ps aux | grep 'from multiprocessing' | grep -v grep | awk '{print $2}' | xargs kill -9 2>/dev/null || true

REMAINING=$(ps aux | grep 'from multiprocessing' | grep -v grep | wc -l | tr -d ' ')
echo ""
echo "Cleanup complete. Remaining processes: $REMAINING"
