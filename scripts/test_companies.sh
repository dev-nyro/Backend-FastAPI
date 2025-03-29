#!/bin/bash

# First ensure we have a fresh token
./scripts/get_token.sh

# Test the endpoint with trailing slash
echo -e "\nTesting with trailing slash:"
curl -v -X GET "http://localhost:8000/companies/" \
-H "Authorization: Bearer $TOKEN" \
-H "Accept: application/json"

# Test the endpoint without trailing slash
echo -e "\nTesting without trailing slash:"
curl -v -X GET "http://localhost:8000/companies" \
-H "Authorization: Bearer $TOKEN" \
-H "Accept: application/json"
