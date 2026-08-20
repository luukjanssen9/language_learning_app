#!/bin/sh
set -e

# Railway (and most PaaS host env-var UIs) have no file-upload secret
# mechanism -- the TTS service-account keyfile is passed as the *content*
# of GOOGLE_APPLICATION_CREDENTIALS_JSON instead and materialized to disk
# here. Local docker-compose already bind-mounts the real file and points
# GOOGLE_APPLICATION_CREDENTIALS at it directly (see docker-compose.yml),
# so this only fires when that file isn't already present.
CRED_PATH="${GOOGLE_APPLICATION_CREDENTIALS:-/app/gcp-tts-credentials.json}"
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS_JSON" ] && [ ! -f "$CRED_PATH" ]; then
  printf '%s' "$GOOGLE_APPLICATION_CREDENTIALS_JSON" > "$CRED_PATH"
  export GOOGLE_APPLICATION_CREDENTIALS="$CRED_PATH"
fi

# Railway assigns the listen port dynamically via $PORT; falls back to
# 8000 (matching the dev Dockerfile/docker-compose) for any other host
# that doesn't set it. No --reload here -- see Dockerfile.prod's own
# comment for why this is a separate image from the dev one.
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
