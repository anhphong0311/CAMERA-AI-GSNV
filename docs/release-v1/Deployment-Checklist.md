# Deployment Checklist — v1.0.0

## Pre-deployment

- [ ] Server meets requirements (16GB RAM, Docker 24+)
- [ ] Domain configured (optional for internal)
- [ ] `.env.production` created with strong secrets
- [ ] SSL certificates generated or Let's Encrypt configured
- [ ] GPU driver + CUDA installed (if using GPU)
- [ ] Telegram bot token obtained (optional)

## Infrastructure

- [ ] PostgreSQL — container healthy
- [ ] Redis — container healthy, password set
- [ ] Backend — health check pass
- [ ] AI Worker — pipeline running
- [ ] Frontend — static files served
- [ ] Nginx — HTTPS redirect working
- [ ] Prometheus — scraping /metrics
- [ ] Grafana — dashboard loaded
- [ ] Watchdog — polling health (if Telegram configured)

## Database

- [ ] `alembic upgrade head` executed
- [ ] Admin user login verified
- [ ] Backup directory writable

## Network

- [ ] Port 443 open (HTTPS)
- [ ] Port 80 redirects to 443
- [ ] RTSP cameras reachable from AI worker network
- [ ] Firewall blocks direct postgres/redis access

## Post-deployment

- [ ] `/api/v1/health/full` returns healthy
- [ ] WebSocket connects through Nginx
- [ ] Test camera stream visible
- [ ] Test rule fires and Telegram delivers
- [ ] Backup cron enabled (optional)
- [ ] Monitoring alerts configured
