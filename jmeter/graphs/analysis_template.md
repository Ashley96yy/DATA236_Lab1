# Lab 2 JMeter Analysis Template

Use this file to summarize the final JMeter findings after running the tests.

## Endpoints Tested
- `POST /api/v1/auth/login`
- `GET /api/v1/restaurants`
- `POST /api/v1/restaurants/{restaurant_id}/reviews`

## Concurrency Levels
- 100 users
- 200 users
- 300 users
- 400 users
- 500 users

## Metrics Recorded
- Average response time
- Throughput
- Error rate

## Analysis Notes

### Login
- Expected trend:
- Observed bottleneck:
- Error behavior:

### Restaurant Search
- Expected trend:
- Observed bottleneck:
- Error behavior:

### Create Review
- Expected trend:
- Observed bottleneck:
- Error behavior:

## Final Summary
- Which endpoint scaled best:
- Which endpoint degraded fastest:
- Likely reason for the performance pattern:
- Suggested optimization:

