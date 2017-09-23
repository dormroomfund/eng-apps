#!/bin/bash
if [ -z "$PORT" ]; then
	echo "Missing PORT environment variable."
	exit 1
fi

# assumes ruby 1.9.2+
ruby -run -ehttpd . -p$PORT &
echo "http://localhost:$PORT"