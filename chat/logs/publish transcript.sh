#!/bin/bash
# Regenerates chat/logs/ALL_SESSIONS_TRANSCRIPT.md from every session_*.jsonl
# file, then commits and pushes both the new session log and the refreshed
# transcript to GitHub. Run this once, after a chat test session, instead
# of running build_transcript.py and then committing/pushing by hand.
#
# Usage (from the repo root, in the Codespaces terminal):
#   bash chat/logs/publish_transcript.sh
#
# Safe to re-run: if there's nothing new to commit, it says so and exits
# cleanly rather than erroring.

set -e

echo "Rebuilding ALL_SESSIONS_TRANSCRIPT.md..."
python chat/logs/build_transcript.py

echo "Staging chat/logs/ changes..."
git add chat/logs/session_*.jsonl chat/logs/ALL_SESSIONS_TRANSCRIPT.md 2>/dev/null || true

if git diff --cached --quiet; then
    echo "Nothing new to commit -- transcript and logs are already up to date."
    exit 0
fi

echo "Committing..."
git commit -m "Update chat test session log and transcript"

echo "Pushing to GitHub..."
git push

echo "Done. Check chat/logs/ALL_SESSIONS_TRANSCRIPT.md on GitHub."
