#!/bin/bash

#!/bin/bash

ENV_FILE=".env"
TEMP_FILE=".env.tmp"

if [ ! -f "$ENV_FILE" ]; then
  echo "❌ No .env file found in the current directory."
  exit 1
fi

echo "🔧 Editing .env file: $ENV_FILE"
echo "-------------------------------"

> "$TEMP_FILE"  # Clear or create temp file

while IFS= read -r line || [[ -n "$line" ]]; do
  # Skip comments and empty lines
  if [[ "$line" =~ ^\s*# || -z "$line" ]]; then
    echo "$line" >> "$TEMP_FILE"
    continue
  fi

  # Parse key and value
  IFS='=' read -r key value <<< "$line"

  echo "Current: $key=$value"
  read -p "Enter new value for $key (leave empty to keep current): " new_value

  if [ -z "$new_value" ]; then
    echo "$key=$value" >> "$TEMP_FILE"
  else
    echo "$key=$new_value" >> "$TEMP_FILE"
  fi
done < "$ENV_FILE"

# Confirm before replacing
echo
read -p "⚠️  Overwrite original .env file with changes? (y/n): " confirm
if [[ "$confirm" =~ ^[Yy]$ ]]; then
  mv "$TEMP_FILE" "$ENV_FILE"
  echo "✅ .env file updated."
else
  rm "$TEMP_FILE"
  echo "❌ Changes discarded."
fi
