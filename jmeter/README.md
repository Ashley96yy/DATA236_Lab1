# Lab 2 JMeter Assets

This folder contains JMeter files for Lab 2.

- `plans/` for `.jmx` test plans
- `data/` for generated CSV test users
- `results/` for raw outputs and summaries
- `graphs/` for exported charts and report-ready visuals

## Included Test Plans

- `plans/login_load_test.jmx`
- `plans/search_load_test.jmx`
- `plans/create_review_load_test.jmx`

These plans target the required Lab 2 endpoints:

- `POST /api/v1/auth/login`
- `GET /api/v1/restaurants`
- `POST /api/v1/restaurants/{restaurant_id}/reviews`

## Before Running JMeter

1. Start the Lab 2 stack:

```bash
docker compose up -d --build
```

2. Seed dedicated load-test accounts and restaurants:

```bash
cd backend
PYTHONPATH=. .venv/bin/python scripts/seed_jmeter_users.py
```

This script creates:
- 500 load-test users
- 500 dedicated restaurants for review creation
- `jmeter/data/load_test_users.csv`

Default load-test password:

```text
Passw0rd!
```

## Example JMeter CLI Commands

Login:

```bash
jmeter -n -t jmeter/plans/login_load_test.jmx \
  -Jthreads=100 \
  -Jramp_up=20 \
  -Jloops=1 \
  -Jresults_file=jmeter/results/login_100.jtl
```

Search:

```bash
jmeter -n -t jmeter/plans/search_load_test.jmx \
  -Jthreads=100 \
  -Jramp_up=20 \
  -Jloops=1 \
  -Jresults_file=jmeter/results/search_100.jtl
```

Create review:

```bash
jmeter -n -t jmeter/plans/create_review_load_test.jmx \
  -Jthreads=100 \
  -Jramp_up=20 \
  -Jloops=1 \
  -Juser_csv=jmeter/data/load_test_users.csv \
  -Jresults_file=jmeter/results/create_review_100.jtl
```

Repeat each plan with:

- `-Jthreads=100`
- `-Jthreads=200`
- `-Jthreads=300`
- `-Jthreads=400`
- `-Jthreads=500`

## Suggested Output Files

- `results/performance_summary_template.csv`
- `graphs/analysis_template.md`

Use those files to consolidate:
- average response time
- throughput
- error rate
- final observations for the report

## Optional Result Summarizer

After generating a `.jtl` file, you can summarize it with:

```bash
python jmeter/scripts/summarize_jtl.py jmeter/results/login_100.jtl
```

This prints:
- sample count
- average response time
- throughput (requests/sec)
- error rate
