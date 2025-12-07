# Scripts

This directory contains utility scripts for managing the application infrastructure.

## pg-idle-stop.sh

A bash script that monitors the PostgreSQL container for active connections and automatically stops it when idle.

### Purpose
- Reduces resource consumption by stopping PostgreSQL when not in use
- Useful for development environments or cost optimization
- Prevents unnecessary CPU/memory usage during idle periods

### How It Works
1. Connects to the PostgreSQL container
2. Queries `pg_stat_activity` to count non-idle connections
3. Stops the container if no active connections are found
4. Logs activity with timestamps

### Setup

1. Make the script executable:
```bash
chmod +x scripts/pg-idle-stop.sh
```

2. Set required environment variables (or configure in docker-compose):
```bash
export POSTGRES_USER=shortener
export POSTGRES_DB=shortener_dev
```

3. Test the script manually:
```bash
./scripts/pg-idle-stop.sh
```

### Automated Monitoring with Cron

To automatically check every 5 minutes, add to your crontab:

```bash
# Edit crontab
crontab -e

# Add this line (adjust path as needed):
*/5 * * * * cd /Volumes/Data\ 1/Uni/WOC7024/woc7004 && ./scripts/pg-idle-stop.sh >> /tmp/pg-idle-stop.log 2>&1
```

### Configuration

Edit the script to customize:
- `CONTAINER`: Name of the PostgreSQL Docker container (default: "postgres")
- `IDLE_MINUTES`: Currently set but not used in logic (can be extended for time-based checks)

### Requirements
- Docker installed and running
- PostgreSQL container named "postgres" (or update `CONTAINER` variable)
- `POSTGRES_USER` and `POSTGRES_DB` environment variables set
- Appropriate permissions to execute Docker commands

### Notes
- The script assumes the container is named "postgres"
- Environment variables must be accessible when running via cron
- Consider using absolute paths in cron jobs
- Review logs to monitor script behavior
