# DATA236 Lab 1 - Yelp Prototype

This repository currently includes the project planning docs and MySQL scripts for the MVP data model.

## Database Setup

### Prerequisites
- MySQL 8.0+
- A MySQL user with permissions to create databases and tables

### Files
- `db/001_init_schema.sql`: create database and tables
- `db/002_seed_sample_data.sql`: insert sample users/restaurants/reviews/favorites/history
- `db/003_quick_check_queries.sql`: quick verification queries

### Run Steps
1. Initialize schema:
```bash
mysql -u <username> -p < db/001_init_schema.sql
```
2. Seed sample data:
```bash
mysql -u <username> -p < db/002_seed_sample_data.sql
```
3. Run quick checks:
```bash
mysql -u <username> -p < db/003_quick_check_queries.sql
```

### Seed Login Accounts
- `alice@example.com` / `Passw0rd!`
- `bob@example.com` / `Passw0rd!`

### Notes
- Database name: `yelp_lab1`
- The seed script is designed to be mostly idempotent for core entities.
