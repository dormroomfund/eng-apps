#!/bin/bash
if [ -z "$PORT" ]; then
	echo "Missing PORT environment variable."
	exit 1
fi

# assumes ruby 1.9.2+
ruby -run -ehttpd $(dirname "$0") -p$PORT &
echo "http://127.0.0.1:$PORT"