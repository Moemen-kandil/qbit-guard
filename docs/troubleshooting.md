# Troubleshooting Guide

This guide covers common issues, debugging techniques, and solutions for qbit-guard deployment and operation.

---

## Container Issues

### Container Fails to Start

**Symptoms**: Container exits immediately or fails to start

```bash
# Check container logs
docker-compose logs qbit-guard
```

**Common causes**:
- Invalid environment variables (check `QBIT_HOST`, credentials)
- Network connectivity issues between containers  
- Missing required environment variables (`SONARR_APIKEY`, etc.)

**Solutions**:
1. Verify all required environment variables are set
2. Check `QBIT_HOST` is accessible from the container
3. Ensure qBittorrent WebUI is enabled and reachable
4. Validate API keys for Sonarr/Radarr

### qbit-guard Cannot Connect to qBittorrent

**Symptoms**: `qB: login failed` or connection timeouts

```bash
# Verify qBittorrent is accessible from qbit-guard container
docker-compose exec qbit-guard wget -qO- http://qbittorrent:8080/api/v2/app/version

# Check network configuration
docker-compose exec qbit-guard nslookup qbittorrent

# Verify credentials and ports match qBittorrent WebUI settings
```

**Solutions**:
1. Check `QBIT_HOST` URL format: `http://qbittorrent:8080`
2. Verify `QBIT_USER` and `QBIT_PASS` match WebUI credentials
3. Ensure qBittorrent WebUI is enabled (Options → Web UI)
4. Check firewall/network connectivity between containers

### No Torrents Being Processed

**Symptoms**: Container runs but doesn't process any torrents

```bash
# Check if torrents are in allowed categories
docker-compose exec qbit-guard printenv QBIT_ALLOWED_CATEGORIES

# Enable debug logging for detailed information  
docker-compose up -d --environment LOG_LEVEL=DEBUG qbit-guard

# Verify polling is working
docker-compose logs -f qbit-guard | grep "Watcher.*started"
```

**Solutions**:
1. Verify `QBIT_ALLOWED_CATEGORIES` matches torrent categories exactly
2. Check that torrents exist in qBittorrent
3. Ensure categories are spelled correctly (case-sensitive)
4. Verify container has polling enabled (`WATCH_POLL_SECONDS` > 0)

---

## API Integration Issues

### Sonarr/Radarr API Timeouts

**Symptoms**: API calls timeout or fail

```bash
# Test connectivity from container
docker-compose exec qbit-guard wget -qO- http://sonarr:8989/api/v3/system/status

# Check for DNS resolution issues
docker-compose exec qbit-guard nslookup sonarr
```

**Solutions**:
1. Increase timeout values:
   ```yaml
   environment:
     - SONARR_TIMEOUT_SEC=90
     - RADARR_TIMEOUT_SEC=90
   ```
2. Use direct container/pod IPs instead of service names if DNS is slow
3. Avoid routing through reverse proxies for *arr API calls
4. Check network latency between containers

### "Pre-air: No Sonarr history" Messages

**Symptoms**: Frequent messages about missing Sonarr history

**Root Cause**: Sonarr may not have written history yet, or there are communication issues

**Solutions**:
1. Set `RESUME_IF_NO_HISTORY=1` (default) to proceed anyway
2. Check Sonarr logs for download client communication issues
3. Verify Sonarr → qBittorrent connection is working
4. Increase `SONARR_TIMEOUT_SEC` if Sonarr is slow to respond

### Internet API Failures

**Symptoms**: TVmaze or TheTVDB API errors

**TVmaze Issues**:
- No auth required, check connectivity to `api.tvmaze.com`
- Increase `TVMAZE_TIMEOUT_SEC` if network is slow

**TheTVDB Issues**:
- Verify `TVDB_APIKEY` and optional `TVDB_PIN` are correct
- Check TheTVDB API status
- Ensure bearer token hasn't expired

**Workaround**: Set `INTERNET_CHECK_PROVIDER=off` to disable cross-checking

---

## Container Networking Problems

### Services Cannot Reach Each Other

```bash
# Verify all services are on the same network
docker network inspect $(docker-compose config --volumes)

# Check if services can reach each other
docker-compose exec qbit-guard ping qbittorrent
docker-compose exec qbit-guard ping sonarr

# Ensure no conflicting container names
docker ps -a | grep -E "(qbittorrent|sonarr|radarr|qbit-guard)"
```

**Solutions**:
1. Ensure all services use the same Docker network
2. Use container service names (not localhost/IP addresses)
3. Check for port conflicts
4. Verify firewall rules aren't blocking container communication

---

## Metadata and File Processing Issues

### Metadata Never Loads

**Symptoms**: Torrents get stuck waiting for metadata (especially magnets)

**Debugging**:
```bash
# Check qBittorrent logs for tracker/DHT issues
docker-compose logs qbittorrent | grep -i tracker
```

**Solutions**:
1. Increase `METADATA_MAX_WAIT_SEC` or set to 0 for infinite wait
2. Verify magnet has sufficient seeds/peers
3. Try reducing `METADATA_POLL_INTERVAL` to 0.5 for faster checking
4. Check qBittorrent's tracker/DHT settings
5. Set download budget limit:
   ```yaml
   environment:
     - METADATA_DOWNLOAD_BUDGET_BYTES=52428800  # 50MB limit
   ```

### Categories Not Processed

**Symptoms**: Torrents in correct categories aren't being processed

**Solutions**:
1. Ensure category names in `QBIT_ALLOWED_CATEGORIES` exactly match qBittorrent categories
2. Categories are normalized to lowercase for comparison
3. Check qBittorrent logs to verify script is being called with correct parameters
4. Use `LOG_LEVEL=DEBUG` to see category matching logic

---

## Performance Issues

### High Resource Usage

**Solutions**:

1. **Reduce polling frequency**:
   ```yaml
   environment:
     - WATCH_POLL_SECONDS=10.0  # Check every 10 seconds instead of 3
   ```

2. **Limit metadata download**:
   ```yaml
   environment:
     - METADATA_MAX_WAIT_SEC=120              # 2 minute timeout
     - METADATA_DOWNLOAD_BUDGET_BYTES=52428800  # 50MB limit
   ```

3. **Set resource limits**:
   ```yaml
   services:
     qbit-guard:
       deploy:
         resources:
           limits:
             memory: 512M        # qbit-guard is lightweight
             cpus: '0.5'
           reservations:
             memory: 128M
             cpus: '0.1'
   ```

### Container Restart Issues

**Process existing torrents after restart**:
```yaml
environment:
  - WATCH_PROCESS_EXISTING_AT_START=1  # Useful after container restarts
```

**Set appropriate restart policy**:
```yaml
services:
  qbit-guard:
    restart: unless-stopped  # Recommended
    # restart: always        # Alternative for critical setups
```

---

## Health Monitoring

### Check Container Health

```bash
# View recent logs
docker-compose logs --tail=50 qbit-guard

# Monitor for healthy operation indicators
docker-compose logs qbit-guard | grep -E "(login OK|Started torrent|Watcher.*started)"

# Watch for error patterns
docker-compose logs qbit-guard | grep -E "(ERROR|Unhandled error|failed)"
```

### Log Indicators

**Success Indicators**:
- ✅ `qB: login OK` - Authentication successful
- ✅ `Started torrent ... after checks` - Normal allow path
- ✅ `Watcher.*started` - Polling mode active

**Expected Blocking Behavior**:
- ⚠️ `Pre-air: BLOCK` - Expected pre-air blocking behavior
- ⚠️ `ISO cleanup: removing` - Expected ISO cleanup

**Error Indicators**:
- ❌ `Unhandled error` - Configuration or connectivity issue
- ❌ `qB: login failed` - Authentication problem
- ❌ `Timeout` - Network connectivity issues

---

## Debug Mode

### Enable Detailed Logging

```yaml
environment:
  - LOG_LEVEL=DEBUG
```

Debug mode shows:
- HTTP request/response details
- Sonarr/Radarr API communication
- File analysis decisions
- Whitelist matching logic
- Metadata fetch progress

### Testing Mode

Use dry-run mode to test configuration without deleting torrents:

```yaml
environment:
  - QBIT_DRY_RUN=1
  - LOG_LEVEL=DEBUG
```

Example dry-run output:
```
2025-01-15 12:00:00 | INFO | DRY-RUN: would delete torrent abc123... due to pre-air (reason=block).
2025-01-15 12:00:00 | INFO | DRY-RUN: would remove torrent def456... (ISO/BDMV-only).
```

---

## Common Configuration Issues

### Environment Variable Problems

**Issue**: Variables not being read properly

```bash
# Check environment in container
docker-compose exec qbit-guard printenv | grep QBIT_

# Verify boolean values
docker-compose exec qbit-guard printenv | grep ENABLE_
```

**Solutions**:
1. Use quotes around values with special characters
2. Boolean values should be `0` or `1`, not `true`/`false`
3. Ensure no extra spaces in environment variable definitions

### Category Matching Issues

**Issue**: Torrents in correct categories aren't processed

```bash
# Check exact category names
docker-compose exec qbit-guard printenv QBIT_ALLOWED_CATEGORIES

# Compare with qBittorrent categories (case-sensitive)
```

**Solutions**:
1. Use exact category names from qBittorrent
2. Separate multiple categories with commas (no spaces)
3. Categories are case-sensitive in configuration

---

## Emergency Procedures

### Stop Processing Immediately

```bash
# Pause the container
docker-compose pause qbit-guard

# Or stop it completely
docker-compose stop qbit-guard
```

### Reset to Safe Mode

```bash
# Enable dry-run mode
docker-compose up -d --environment QBIT_DRY_RUN=1 qbit-guard

# Or disable all processing temporarily
docker-compose up -d --environment QBIT_ALLOWED_CATEGORIES= qbit-guard
```

### Recover from Bad Configuration

1. **Stop qbit-guard**: `docker-compose stop qbit-guard`
2. **Fix configuration** in docker-compose.yml
3. **Test with dry-run**: Add `QBIT_DRY_RUN=1`
4. **Restart**: `docker-compose up -d qbit-guard`
5. **Monitor logs**: `docker-compose logs -f qbit-guard`

---

## Getting Help

### Collect Diagnostic Information

When seeking help, provide:

1. **Container logs**:
   ```bash
   docker-compose logs --tail=100 qbit-guard > qbit-guard-logs.txt
   ```

2. **Configuration** (sanitized):
   ```bash
   docker-compose config > docker-compose-config.yml
   # Remove sensitive info like passwords/API keys
   ```

3. **Environment details**:
   - Docker and Docker Compose versions
   - Operating system
   - Network setup (bridge, host, etc.)
   - qBittorrent version

4. **Steps to reproduce** the issue

### Best Practices for Support

1. **Enable debug mode** first: `LOG_LEVEL=DEBUG`
2. **Test with dry-run**: `QBIT_DRY_RUN=1`
3. **Isolate the issue**: Test with minimal configuration
4. **Check logs thoroughly** before asking for help
5. **Provide specific error messages** and log excerpts

---

## Next Steps

- **[Development Guide →](usage/dev.md)** - Advanced debugging techniques
- **[Configuration Guide →](usage/configure.md)** - Review configuration options
- **[Examples →](examples.md)** - Working configurations for reference