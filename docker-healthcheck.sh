#!/usr/bin/env bash
PORT=${HTTPS_PORT:-443}
curl --max-time 5 -kILs --fail https://localhost:${PORT}
