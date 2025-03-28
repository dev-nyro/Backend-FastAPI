#!/bin/bash

response=$(curl -s -X POST http://localhost:8000/auth/login \
-H "Content-Type: application/x-www-form-urlencoded" \
-d "username=admin@test.com" \
-d "password=adminpass123")

echo "Full server response: $response"

# Decode and show token content
token=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    token = data.get('access_token', '')
    print(token)
    if token:
        import base64
        parts = token.split('.')
        if len(parts) > 1:
            padding = '=' * (4 - len(parts[1]) % 4)
            payload = base64.b64decode(parts[1] + padding).decode('utf-8')
            print('\nToken payload:', payload, file=sys.stderr)
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    exit(1)
")

# Save and export token if we got one
if [ ! -z "$token" ]; then
    echo "$token" > token.txt
    export TOKEN="$token"
    echo "Token saved and exported"
fi
