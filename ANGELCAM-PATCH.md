# Angelcam patch

This fork is upstream nginx-proxy 1.11.6 with a single change: the base image in
`Dockerfile.debian` is bumped from `nginx:1.31.3` to `nginx:1.31.9`.

Why: nginx CVE-2026-123007, CVE-2026-123633, CVE-2026-121810, CVE-2026-123634 and
CVE-2026-113425 are fixed in nginx 1.31.9+ / 1.30.7+ (https://nginx.org/en/security_advisories.html).
No upstream nginx-proxy release ships a fixed nginx yet (https://github.com/nginx-proxy/nginx-proxy/issues/2791,
PR #2792). `ENABLE_HTTP2=false` is not enough because the fallback server keeps `http2 on;`.

Image: angelcam/nginx-proxy-patched:1.11.6-nginx1.31.9

Switch back to the upstream image `nginxproxy/nginx-proxy` once a release ships nginx >= 1.31.9.