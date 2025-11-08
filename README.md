# Performance Testing: Redis vs Database

This project provides a simple setup to compare the performance of Redis caching against a database.

## Prerequisites

- Docker (for running PostgreSQL and Redis)
- Make
- K6 (for load testing)

## Setup

Run the following command to set up the environment:

```bash
make setup
```

**What this does:**

- Starts PostgreSQL and Redis using Docker.
- Seeds Redis with initial data and URLs to simulate cached content.
- Prepares the database with necessary records.
- Ensures that both the database and Redis are ready for performance testing.

This setup ensures that the load tests can simulate realistic conditions where some requests can be served from Redis (cache) while others hit the database.

## Load Testing

After setup, run the performance tests with:

```bash
make loadtest
```

**What this does:**

- Runs K6 load tests that simulate multiple virtual users (VUs) making requests.
- Compares performance between requests served from Redis (cache) and requests served directly from the database.
- Uses the `per-vu-iterations` executor to simulate multiple requests per user.
- Collects metrics like response times, throughput (requests per second), and error rates.

This allows you to measure the performance difference between cached and non-cached requests under simulated load.

## Results

Test results are stored in:

```bash
k6/results
```

You can analyze these results to see:

- How much faster Redis responds compared to the database.
- Whether caching reduces errors under load.
- Throughput improvements with Redis.

## Project Structure

- `Makefile` – Contains commands for setup (`make setup`) and load testing (`make loadtest`)
- `k6/` – Contains K6 load test scripts and results
- `db/` – Database setup and seed scripts
- `redis/` – Redis seed scripts

## Notes

- Make sure Docker is running before executing `make setup`.
- K6 scripts can be customized in the `k6/` folder if needed.
- The load test uses the `per-vu-iterations` executor to simulate realistic concurrent load. Adjust the number of VUs and iterations in the scripts to match your testing requirements.

## Example Usage

```bash
# Setup environment
make setup

# Run performance tests
make loadtest

# Check results
ls k6/results
```

## Summary

This project allows you to quickly compare database queries versus cached data in Redis under simulated load conditions. By analyzing the results, you can:

- Identify performance bottlenecks
- Measure the impact of caching on response times
- Optimize your application for better scalability
