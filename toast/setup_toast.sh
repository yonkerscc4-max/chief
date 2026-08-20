#!/usr/bin/env bash
# Toast API setup for Yonkers Brewing Co.
# Run once:  bash setup_toast.sh
# Prompts for the four credential values, writes ~/.config/toast/credentials.env
# with 600 permissions, and verifies the connection.

set -euo pipefail

CRED_DIR="$HOME/.config/toast"
CRED_FILE="$CRED_DIR/credentials.env"

echo "Toast API setup"
echo "==============="
echo
if [ -f "$CRED_FILE" ]; then
  read -r -p "$CRED_FILE already exists. Overwrite? [y/N] " ok
  [[ "${ok:-N}" =~ ^[Yy]$ ]] || { echo "Left it alone. Nothing changed."; exit 0; }
fi

echo "Paste each value from the Toast Web credentials page."
echo "The secret is hidden as you type, which is expected."
echo

read -r -p  "TOAST_CLIENT_ID            : " CLIENT_ID
read -rs -p "TOAST_CLIENT_SECRET        : " CLIENT_SECRET; echo
read -r -p  "TOAST_RESTAURANT_GUID      : " RESTAURANT_GUID
read -r -p  "TOAST_MANAGEMENT_GROUP_GUID: " MGMT_GUID

for pair in "CLIENT_ID:$CLIENT_ID" "CLIENT_SECRET:$CLIENT_SECRET" "RESTAURANT_GUID:$RESTAURANT_GUID"; do
  if [ -z "${pair#*:}" ]; then echo "ERROR: ${pair%%:*} cannot be empty."; exit 1; fi
done

mkdir -p "$CRED_DIR"
umask 077
cat > "$CRED_FILE" <<EOF
TOAST_API_HOSTNAME=https://ws-api.toasttab.com
TOAST_CLIENT_ID=$CLIENT_ID
TOAST_CLIENT_SECRET=$CLIENT_SECRET
TOAST_USER_ACCESS_TYPE=TOAST_MACHINE_CLIENT
TOAST_RESTAURANT_GUID=$RESTAURANT_GUID
TOAST_MANAGEMENT_GROUP_GUID=$MGMT_GUID
EOF
chmod 600 "$CRED_FILE"

echo
echo "Wrote $CRED_FILE (permissions 600, readable only by you)."
echo

if [ -f "./toast_client.py" ]; then
  echo "Verifying the connection..."
  echo
  python3 ./toast_client.py
else
  echo "Put toast_client.py in this folder and run:  python3 toast_client.py"
  echo "That verifies the connection and prints the restaurant name."
fi
