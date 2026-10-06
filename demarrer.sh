#!/bin/sh
# Lance le gestionnaire de podcast (macOS / Linux)
cd "$(dirname "$0")"
( sleep 1; (open http://localhost:3000 2>/dev/null || xdg-open http://localhost:3000 2>/dev/null) ) &
node server.js
