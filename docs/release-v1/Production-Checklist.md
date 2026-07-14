# Production Checklist — v1.0.0

## Camera

- [ ] All cameras registered in config
- [ ] RTSP URLs verified
- [ ] Reconnect policy tested
- [ ] FPS within expected range (15–30)

## AI

- [ ] YOLO model weights in `/models`
- [ ] Detection confidence threshold tuned
- [ ] GPU utilization < 90% at peak

## Tracking

- [ ] Track IDs stable across frames
- [ ] ROI zones configured per camera

## Rule Engine

- [ ] Rules loaded from `config/rules.yaml`
- [ ] Cooldown periods appropriate
- [ ] Test events fire correctly

## Alert

- [ ] Telegram bot responding
- [ ] Snapshots saving to evidence folder
- [ ] Video ring buffer recording

## Dashboard

- [ ] All 16 pages load
- [ ] WebSocket real-time updates
- [ ] Login/auth working for all roles

## Monitoring

- [ ] Prometheus targets UP
- [ ] Grafana AEMS Overview dashboard
- [ ] Watchdog alerts tested

## Backup

- [ ] Manual backup tested
- [ ] Restore procedure documented and tested
- [ ] Off-site backup copy scheduled

## Restore

- [ ] Restore script verified on staging
- [ ] RTO/RPO documented in Disaster Recovery guide
