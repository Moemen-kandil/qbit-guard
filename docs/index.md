# qbit-guard

A zero-dependency Python guard for qBittorrent that provides intelligent torrent management with pre-air checking and ISO/BDMV cleanup.

## Features

- **Pre-air gate (Sonarr)**: Stops new TV torrents, checks airDateUtc with configurable grace periods, supports release group/indexer/tracker whitelisting, and blocks torrents that are too early
- **ISO/BDMV cleaner**: After metadata arrives, removes disc-image-only torrents (ISO, IMG, MDF, NRG, CUE, BIN files and BDMV/VIDEO_TS folders) that lack keepable video content
- **Smart blocklisting**: Blocklists in Sonarr/Radarr before deletion using deduped history (single "grabbed" record per unique release title) with queue failover if history endpoint times out
- **Internet cross-verification**: Optional TVmaze and/or TheTVDB API integration to cross-check Sonarr air dates
- **Version compatibility**: Works with qBittorrent 5.x (start/stop) and 4.x fallback (resume/pause)
- **Zero dependencies**: No external libraries, just Python 3.8+ stdlib
- **Container-friendly**: All configuration via environment variables, logs to stdout
- **Magnet support**: Handles magnet links by waiting for metadata resolution with configurable timeouts and download budgets

## How it Works

### Detailed Workflow

1. **On torrent add**: Torrent is immediately stopped and tagged (`guard:stopped`)

2. **Category filtering**: Only processes torrents in `QBIT_ALLOWED_CATEGORIES`

3. **Pre-air gate** (if category matches Sonarr categories):
   - Fetches Sonarr history for the download ID (with retry logic)
   - Extracts episode IDs and checks `airDateUtc` from Sonarr
   - **Optional internet cross-check**: Queries TVmaze/TheTVDB APIs to verify air dates
   - **Grace period**: Allows early releases within `EARLY_GRACE_HOURS` (default: 6h)
   - **Whitelist bypass**: Release groups, indexers, or trackers in whitelist can bypass restrictions
   - **Hard cap**: Blocks releases more than `EARLY_HARD_LIMIT_HOURS` early (default: 72h) unless whitelisted
   - **If blocked**: Blocklists in Sonarr using deduped history → queue failover, then deletes torrent
   - **If allowed**: Proceeds to metadata fetch

4. **Metadata fetching** (for file inspection):
   - Temporarily starts torrent to resolve metadata (especially for magnets)
   - Polls `/api/v2/torrents/files` until file list is available
   - Sends periodic reannounce requests to speed up magnet resolution
   - Respects `METADATA_MAX_WAIT_SEC` timeout and `METADATA_DOWNLOAD_BUDGET_BYTES` limits
   - Stops torrent once metadata is obtained

5. **ISO/BDMV cleanup** (if enabled):
   - Analyzes file list for disc image formats and folder structures
   - Identifies torrents with only ISO/BDMV content and no keepable video files
   - **If disc-only**: Blocklists in appropriate Sonarr/Radarr instance, then deletes
   - **Video size threshold**: Only keeps video files ≥ `MIN_KEEPABLE_VIDEO_MB` (default: 50MB)

6. **Final step**: Tags torrent (`guard:allowed`) and starts it for real

### Supported File Formats

**Disc Images (blocked)**: `.iso`, `.img`, `.mdf`, `.nrg`, `.cue`, `.bin`, `BDMV/`, `VIDEO_TS/`  
**Video Files (kept)**: `.mkv`, `.mp4`, `.m4v`, `.avi`, `.ts`, `.m2ts`, `.mov`, `.webm`

## Requirements

- **qBittorrent**: 5.x preferred (4.x supported via API fallback)
- **Python**: 3.8+ (uses dataclasses, type hints, datetime.timezone)
- **Sonarr**: v3 API (optional but recommended for pre-air blocking)
- **Radarr**: v3 API (optional, used for ISO blocklisting)
- **Network**: Direct connectivity between qBittorrent ↔ Sonarr/Radarr (avoid reverse proxy timeouts)
- **Dependencies**: None - pure Python stdlib only

## Installation

qbit-guard can be deployed in two ways: as a containerized service (recommended) or as a traditional script. Choose the method that best fits your setup.

### Docker Installation (Recommended)

The containerized version runs as a standalone service that continuously monitors qBittorrent, eliminating the need for webhook configuration.

#### Quick Start

1. **Pull the official image**:
   ```bash
   docker pull ghcr.io/gengines/qbit-guard:1.0.0
   ```

2. **Create a basic docker-compose.yml**:
   ```yaml
   version: '3.8'
   services:
     qbit-guard:
       image: ghcr.io/gengines/qbit-guard:1.0.0
       container_name: qbit-guard
       restart: unless-stopped
       environment:
         - QBIT_HOST=http://qbittorrent:8080
         - QBIT_USER=admin
         - QBIT_PASS=your_password
         - QBIT_ALLOWED_CATEGORIES=tv-sonarr,radarr
         - ENABLE_PREAIR_CHECK=1
         - SONARR_URL=http://sonarr:8989
         - SONARR_APIKEY=your_api_key
         - LOG_LEVEL=INFO
       networks:
         - arr-network
   
   networks:
     arr-network:
       driver: bridge
   ```

3. **Start the service**:
   ```bash
   docker-compose up -d
   ```

#### Container Modes

**Polling Mode (Default)**: The container continuously polls qBittorrent's API for new torrents. This is the recommended approach as it:
- Requires no qBittorrent webhook configuration
- Works reliably across container restarts
- Handles network interruptions gracefully
- Provides better visibility into processing status

**Webhook Mode**: Configure qBittorrent to call the container on torrent add events. This requires:
- Exposing the container port (`8080:8080`)
- Configuring qBittorrent's "Run external program" setting to call `http://qbit-guard:8080/webhook`
- Additional network connectivity setup
- More complex debugging when issues arise

For most users, polling mode is simpler and more reliable.

> **Note**: A complete working `docker-compose.yml` file is included in the repository root with all configuration options documented.

### Script Installation (Traditional)

For users who prefer the traditional webhook approach or need to customize the deployment:

1. **Download and make executable**:
   ```bash
   curl -o /config/scripts/qbit-guard.py https://raw.githubusercontent.com/GEngines/qbit-guard/main/qbit-guard.py
   chmod +x /config/scripts/qbit-guard.py
   ```

2. **Configure qBittorrent**:
   - Navigate to **Options** → **Downloads** → **Run external program**
   - **Run on torrent added**:
     ```bash
     /usr/bin/python3 /config/scripts/qbit-guard.py %I %L
     ```
   - **Important**: Remove any existing "Run on torrent added" scripts to avoid conflicts

3. **Set environment variables** in your container/docker-compose

4. **Restart qBittorrent**

## Configuration

All configuration is handled via environment variables with sensible defaults.

### Essential qBittorrent Settings

```bash
# qBittorrent connection
QBIT_HOST=http://qbittorrent:8080              # qB WebUI URL
QBIT_USER=admin                                # WebUI username  
QBIT_PASS=adminadmin                          # WebUI password
QBIT_ALLOWED_CATEGORIES="tv-sonarr,radarr"    # Comma-separated categories to process
QBIT_DELETE_FILES=true                        # Delete files when removing torrents
QBIT_IGNORE_TLS=0                            # Set to 1 to ignore SSL certificate errors
QBIT_DRY_RUN=0                               # Set to 1 for testing (no actual deletions)
```

### Sonarr Integration (Pre-air Gate)

```bash
# Enable pre-air checking
ENABLE_PREAIR_CHECK=1
SONARR_URL=http://sonarr:8989
SONARR_APIKEY=your_sonarr_api_key_here
SONARR_CATEGORIES="tv-sonarr"                 # Categories to apply pre-air checks to

# Pre-air timing controls
EARLY_GRACE_HOURS=6                           # Allow releases this many hours before air date
EARLY_HARD_LIMIT_HOURS=72                     # Block releases more than this many hours early
WHITELIST_OVERRIDES_HARD_LIMIT=0             # Set to 1 to let whitelisted releases bypass hard limit

# Whitelisting (comma-separated, case-insensitive)
EARLY_WHITELIST_GROUPS="scene_group1,group2"
EARLY_WHITELIST_INDEXERS="indexer1,indexer2" 
EARLY_WHITELIST_TRACKERS="tracker1,tracker2"

# Fallback behavior
RESUME_IF_NO_HISTORY=1                        # Proceed if Sonarr history not found yet
```

### Internet Cross-Verification (Optional)

```bash
# Provider selection
INTERNET_CHECK_PROVIDER=tvmaze               # off, tvmaze, tvdb, or both

# TVmaze settings (no API key required)
TVMAZE_BASE=https://api.tvmaze.com
TVMAZE_TIMEOUT_SEC=8

# TheTVDB settings (requires API key)
TVDB_BASE=https://api4.thetvdb.com/v4
TVDB_APIKEY=your_tvdb_api_key_here
TVDB_PIN=your_tvdb_pin                       # Optional
TVDB_LANGUAGE=eng                            # Language code
TVDB_ORDER=default                           # default or official
TVDB_TIMEOUT_SEC=8
TVDB_BEARER=                                 # Reuse existing token (optional)
```

### ISO/BDMV Cleanup

```bash
# Enable ISO/disc image cleanup
ENABLE_ISO_CHECK=1

# Video file criteria  
MIN_KEEPABLE_VIDEO_MB=50                     # Minimum size for video files to keep (MB)

# Metadata fetching behavior
METADATA_POLL_INTERVAL=1.5                   # Seconds between file list checks
METADATA_MAX_WAIT_SEC=0                      # Max wait for metadata (0 = infinite)
METADATA_DOWNLOAD_BUDGET_BYTES=0             # Max bytes to download while waiting (0 = no limit)
```

### Radarr Integration (ISO Blocklisting)

```bash
# Radarr connection (for movie ISO cleanup)
RADARR_URL=http://radarr:7878
RADARR_APIKEY=your_radarr_api_key_here
RADARR_CATEGORIES="radarr"                   # Categories to apply Radarr blocklisting to
```

### Reliability & Performance

| Variable | Default | Description |
|----------|---------|-------------|
| `SONARR_TIMEOUT_SEC` | 45 | HTTP timeout for Sonarr API calls |
| `SONARR_RETRIES` | 3 | Retry attempts for Sonarr blocklist operations |
| `RADARR_TIMEOUT_SEC` | 45 | HTTP timeout for Radarr API calls |
| `RADARR_RETRIES` | 3 | Retry attempts for Radarr blocklist operations |
| `USER_AGENT` | `qbit-guard/2.0` | HTTP User-Agent string |
| `LOG_LEVEL` | `INFO` | Logging verbosity (`INFO` or `DEBUG`) |

## Docker Deployment

### Container Networking

qbit-guard needs network connectivity to your *arr services and qBittorrent. The container deployment uses polling mode by default, which only requires outbound connections.

#### Network Requirements

- **qBittorrent API**: HTTP access to qBittorrent's Web UI (default port 8080)
- **Sonarr API**: HTTP access to Sonarr (default port 8989) 
- **Radarr API**: HTTP access to Radarr (default port 7878)
- **Internet APIs**: HTTPS access to TVmaze (api.tvmaze.com) and TheTVDB (api4.thetvdb.com) for cross-verification

#### Docker Compose Networking

Create a shared network for all services:

```yaml
networks:
  arr-network:
    driver: bridge
```

All services (qbit-guard, qbittorrent, sonarr, radarr) should use the same network to enable service discovery by container name.

### Complete Docker Compose Examples

#### Minimal Configuration

Basic setup with essential features only:

```yaml
version: '3.8'

services:
  qbit-guard:
    image: ghcr.io/gengines/qbit-guard:1.0.0
    container_name: qbit-guard
    restart: unless-stopped
    environment:
      # Essential qBittorrent connection
      - QBIT_HOST=http://qbittorrent:8080
      - QBIT_USER=admin
      - QBIT_PASS=your_password_here
      - QBIT_ALLOWED_CATEGORIES=tv-sonarr,radarr
      
      # Basic pre-air checking with Sonarr
      - ENABLE_PREAIR_CHECK=1
      - SONARR_URL=http://sonarr:8989
      - SONARR_APIKEY=your_sonarr_api_key_here
      
      # ISO cleanup
      - ENABLE_ISO_CHECK=1
      
      - LOG_LEVEL=INFO
    networks:
      - arr-network
    depends_on:
      - qbittorrent

  qbittorrent:
    image: lscr.io/linuxserver/qbittorrent:latest
    container_name: qbittorrent
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=UTC
      - WEBUI_PORT=8080
    volumes:
      - ./qbittorrent:/config
      - ./downloads:/downloads
    ports:
      - "8080:8080"
      - "6881:6881"
      - "6881:6881/udp"
    restart: unless-stopped
    networks:
      - arr-network

  sonarr:
    image: lscr.io/linuxserver/sonarr:latest
    container_name: sonarr
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=UTC
    volumes:
      - ./sonarr:/config
      - ./downloads:/downloads
      - ./tv:/tv
    ports:
      - "8989:8989"
    restart: unless-stopped
    networks:
      - arr-network

networks:
  arr-network:
    driver: bridge
```

#### Full Configuration

Advanced setup with all features enabled:

```yaml
version: '3.8'

services:
  qbit-guard:
    image: ghcr.io/gengines/qbit-guard:1.0.0
    container_name: qbit-guard
    restart: unless-stopped
    environment:
      # ===== LOGGING =====
      - LOG_LEVEL=INFO                                    # DEBUG for troubleshooting

      # ===== qBITTORRENT CONNECTION =====
      - QBIT_HOST=http://qbittorrent:8080                
      - QBIT_USER=admin                                   
      - QBIT_PASS=your_secure_password_here             
      - QBIT_ALLOWED_CATEGORIES=tv-sonarr,radarr         
      - QBIT_DELETE_FILES=true                           
      - QBIT_DRY_RUN=0                                   # Set to 1 for testing

      # ===== POLLING CONFIGURATION =====
      - WATCH_POLL_SECONDS=3.0                          # How often to check for new torrents
      - WATCH_PROCESS_EXISTING_AT_START=0                # Process existing torrents on startup
      - WATCH_RESCAN_KEYWORD=rescan                      # Keyword in category/tags to force reprocess

      # ===== PRE-AIR CHECKING (SONARR) =====
      - ENABLE_PREAIR_CHECK=1                            
      - SONARR_URL=http://sonarr:8989                    
      - SONARR_APIKEY=your_sonarr_api_key_here           
      - SONARR_CATEGORIES=tv-sonarr                      
      - EARLY_GRACE_HOURS=6                              # Allow releases 6h before air
      - EARLY_HARD_LIMIT_HOURS=72                        # Block releases >72h early
      - WHITELIST_OVERRIDES_HARD_LIMIT=0                 
      - EARLY_WHITELIST_GROUPS=trusted_group1,trusted_group2
      - EARLY_WHITELIST_INDEXERS=                        
      - EARLY_WHITELIST_TRACKERS=                        
      - RESUME_IF_NO_HISTORY=1                           
      - SONARR_TIMEOUT_SEC=45                            
      - SONARR_RETRIES=3                                 

      # ===== INTERNET CROSS-VERIFICATION =====
      - INTERNET_CHECK_PROVIDER=both                     # off, tvmaze, tvdb, or both
      - TVMAZE_TIMEOUT_SEC=8                            
      - TVDB_APIKEY=your_tvdb_api_key_here               # Required for TVDB
      - TVDB_PIN=your_tvdb_pin                          # Optional
      - TVDB_TIMEOUT_SEC=8                               

      # ===== ISO/BDMV CLEANUP =====
      - ENABLE_ISO_CHECK=1                               
      - MIN_KEEPABLE_VIDEO_MB=50                         # Minimum video file size to keep
      - METADATA_POLL_INTERVAL=1.5                       
      - METADATA_MAX_WAIT_SEC=300                        # 5 minute timeout for metadata
      - METADATA_DOWNLOAD_BUDGET_BYTES=104857600         # 100MB limit for magnet resolution

      # ===== RADARR INTEGRATION =====
      - RADARR_URL=http://radarr:7878                    
      - RADARR_APIKEY=your_radarr_api_key_here           
      - RADARR_CATEGORIES=radarr                         
      - RADARR_TIMEOUT_SEC=45                            
      - RADARR_RETRIES=3                                 

    networks:
      - arr-network
    depends_on:
      - qbittorrent
      - sonarr
      - radarr

  qbittorrent:
    image: lscr.io/linuxserver/qbittorrent:latest
    container_name: qbittorrent
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=UTC
      - WEBUI_PORT=8080
    volumes:
      - ./qbittorrent:/config
      - ./downloads:/downloads
    ports:
      - "8080:8080"
      - "6881:6881"
      - "6881:6881/udp"
    restart: unless-stopped
    networks:
      - arr-network

  sonarr:
    image: lscr.io/linuxserver/sonarr:latest
    container_name: sonarr
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=UTC
    volumes:
      - ./sonarr:/config
      - ./downloads:/downloads
      - ./tv:/tv
    ports:
      - "8989:8989"
    restart: unless-stopped
    networks:
      - arr-network

  radarr:
    image: lscr.io/linuxserver/radarr:latest
    container_name: radarr
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=UTC
    volumes:
      - ./radarr:/config
      - ./downloads:/downloads
      - ./movies:/movies
    ports:
      - "7878:7878"
    restart: unless-stopped
    networks:
      - arr-network

networks:
  arr-network:
    driver: bridge
```

### Container Environment Variables

The containerized version supports all the same environment variables as the script installation, plus additional polling configuration:

#### Container-Specific Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `WATCH_POLL_SECONDS` | `3.0` | How often to check qBittorrent for new torrents |
| `WATCH_PROCESS_EXISTING_AT_START` | `0` | Process existing torrents when container starts |
| `WATCH_RESCAN_KEYWORD` | `rescan` | Keyword in category/tags to force reprocessing |

#### Key Differences from Script Mode

- **No webhook setup required**: Container polls qBittorrent API directly
- **Persistent monitoring**: Runs continuously instead of per-torrent execution
- **Graceful restarts**: Remembers processed torrents during container lifecycle
- **Better logging**: Centralized container logs with structured output
- **Resource efficient**: Single process handles all torrents

## Usage Examples

### Legacy Docker Compose (Script Mode)

For reference, here's how qbit-guard was traditionally used with webhook integration (not recommended for new deployments):

```yaml
services:
  qbittorrent:
    image: lscr.io/linuxserver/qbittorrent:latest
    environment:
      # qBittorrent settings
      - QBIT_HOST=http://qbittorrent:8080
      - QBIT_USER=admin
      - QBIT_PASS=supersecret
      - QBIT_ALLOWED_CATEGORIES=tv-sonarr,radarr
      
      # Pre-air gate
      - ENABLE_PREAIR_CHECK=1
      - SONARR_URL=http://sonarr:8989
      - SONARR_APIKEY=abc123...
      - EARLY_GRACE_HOURS=6
      - EARLY_HARD_LIMIT_HOURS=72
      - EARLY_WHITELIST_GROUPS=scene1,scene2
      
      # Internet verification
      - INTERNET_CHECK_PROVIDER=both
      - TVDB_APIKEY=xyz789...
      
      # ISO cleanup
      - ENABLE_ISO_CHECK=1
      - MIN_KEEPABLE_VIDEO_MB=100
      
      # Radarr integration
      - RADARR_URL=http://radarr:7878
      - RADARR_APIKEY=def456...
      
      - LOG_LEVEL=INFO
    volumes:
      - ./scripts:/config/scripts
```

### Kubernetes ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: qbit-guard-config
data:
  QBIT_HOST: "http://qbittorrent:8080"
  QBIT_ALLOWED_CATEGORIES: "tv-sonarr,radarr"
  ENABLE_PREAIR_CHECK: "1"
  SONARR_URL: "http://sonarr:8989"
  EARLY_GRACE_HOURS: "6"
  INTERNET_CHECK_PROVIDER: "tvmaze"
  ENABLE_ISO_CHECK: "1"
  LOG_LEVEL: "DEBUG"
```

## Monitoring & Operations

### Log Examples

```
2025-01-15 10:30:15 | INFO | Processing: hash=abc123... category='tv-sonarr' name='TV.Show.S01E01.720p'
2025-01-15 10:30:16 | INFO | Pre-air: ALLOW (aired+grace)  
2025-01-15 10:30:18 | INFO | ISO cleaner: content looks OK (keepable=True, files=3)
2025-01-15 10:30:18 | INFO | Started torrent abc123... after checks.

2025-01-15 11:45:22 | INFO | Pre-air: BLOCK_CAP max_future=168.50 h
2025-01-15 11:45:23 | INFO | Sonarr: blocklisted via history id=12345
2025-01-15 11:45:23 | INFO | Pre-air: deleted torrent def456... (reason=cap).
```

### Torrent Tags

The script applies these tags for tracking:
- `guard:stopped` - Initial state when processing begins
- `guard:allowed` - Passed all checks, torrent started
- `trash:preair` - Deleted due to pre-air violation  
- `trash:iso` - Deleted due to ISO/BDMV-only content

### Testing Mode

Set `QBIT_DRY_RUN=1` to test configuration without actually deleting torrents:

```bash
2025-01-15 12:00:00 | INFO | DRY-RUN: would delete torrent abc123... due to pre-air (reason=block).
2025-01-15 12:00:00 | INFO | DRY-RUN: would remove torrent def456... (ISO/BDMV-only).
```

## Important Notes

### Blocklisting Strategy
- **Deduplication**: Only creates one blocklist entry per unique release title (uses newest "grabbed" history record)
- **Failover mechanism**: If `/api/v3/history/failed/{id}` times out, falls back to `/api/v3/queue/{id}?blocklist=true`
- **No duplicates**: Prevents spam in *arr blocklist by tracking source/release titles

### Internet API Behavior  
- **TVmaze**: No API key required, uses TVDB/IMDB/title lookup chain
- **TheTVDB**: Requires API key, supports PIN authentication, caches bearer tokens
- **Cross-check logic**: Takes the **earliest** air date from all sources (Sonarr + internet APIs)

### Metadata Handling
- **Magnet links**: Script waits for torrent client to resolve metadata before analysis
- **Reannounce**: Periodically sends reannounce requests to speed up magnet resolution  
- **Budget controls**: Optional download limits prevent runaway metadata fetching
- **Fast stop**: Stops torrent immediately once file list appears

## Container Troubleshooting

### Common Docker Issues

**Container fails to start**
```bash
# Check container logs
docker-compose logs qbit-guard

# Common causes:
# - Invalid environment variables (check QBIT_HOST, credentials)
# - Network connectivity issues between containers
# - Missing required environment variables (SONARR_APIKEY, etc.)
```

**qbit-guard can't connect to qBittorrent**
```bash
# Verify qBittorrent is accessible from qbit-guard container
docker-compose exec qbit-guard wget -qO- http://qbittorrent:8080/api/v2/app/version

# Check network configuration:
docker-compose exec qbit-guard nslookup qbittorrent

# Verify credentials and ports match qBittorrent WebUI settings
```

**No torrents being processed**
```bash
# Check if torrents are in allowed categories
docker-compose exec qbit-guard printenv QBIT_ALLOWED_CATEGORIES

# Enable debug logging for detailed information
docker-compose up -d --environment LOG_LEVEL=DEBUG qbit-guard

# Verify polling is working
docker-compose logs -f qbit-guard | grep "Watcher.*started"
```

**API timeouts with Sonarr/Radarr**
```bash
# Test connectivity from container
docker-compose exec qbit-guard wget -qO- http://sonarr:8989/api/v3/system/status

# Increase timeout values
- SONARR_TIMEOUT_SEC=90
- RADARR_TIMEOUT_SEC=90

# Check for DNS resolution issues
docker-compose exec qbit-guard nslookup sonarr
```

**Container networking problems**
```bash
# Verify all services are on the same network
docker network inspect $(docker-compose config --volumes)

# Check if services can reach each other
docker-compose exec qbit-guard ping qbittorrent
docker-compose exec qbit-guard ping sonarr

# Ensure no conflicting container names
docker ps -a | grep -E "(qbittorrent|sonarr|radarr|qbit-guard)"
```

### Container Performance Tuning

**Reduce polling frequency for lower resource usage**
```yaml
environment:
  - WATCH_POLL_SECONDS=10.0  # Check every 10 seconds instead of 3
```

**Limit metadata download for large magnet torrents**
```yaml
environment:
  - METADATA_MAX_WAIT_SEC=120              # 2 minute timeout
  - METADATA_DOWNLOAD_BUDGET_BYTES=52428800  # 50MB limit
```

**Process existing torrents on container start**
```yaml
environment:
  - WATCH_PROCESS_EXISTING_AT_START=1  # Useful after container restarts
```

### Container Health Monitoring

**Check container health**
```bash
# View recent logs
docker-compose logs --tail=50 qbit-guard

# Monitor for healthy operation indicators
docker-compose logs qbit-guard | grep -E "(login OK|Started torrent|Watcher.*started)"

# Watch for error patterns
docker-compose logs qbit-guard | grep -E "(ERROR|Unhandled error|failed)"
```

**Container restart policies**
```yaml
services:
  qbit-guard:
    restart: unless-stopped  # Recommended
    # restart: always        # Alternative for critical setups
```

**Resource limits**
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

## Troubleshooting

### Common Issues

**"Pre-air: No Sonarr history" messages**
- Sonarr may not have written history yet - script retries 5 times with delays
- Set `RESUME_IF_NO_HISTORY=1` (default) to proceed anyway
- Check Sonarr logs for download client communication issues

**Blocklist timeouts**  
- Increase `SONARR_TIMEOUT_SEC`/`RADARR_TIMEOUT_SEC` (try 90+)
- Use direct container/pod IPs instead of service names if DNS is slow
- Avoid routing through reverse proxies for *arr API calls

**Metadata never loads**
- Check qBittorrent logs for tracker/DHT issues
- Increase `METADATA_MAX_WAIT_SEC` or set to 0 for infinite wait
- Verify magnet has sufficient seeds/peers
- Try reducing `METADATA_POLL_INTERVAL` to 0.5 for faster checking

**Internet API failures**
- TVmaze: No auth required, check connectivity to `api.tvmaze.com`
- TheTVDB: Verify API key and optional PIN are correct
- Set `INTERNET_CHECK_PROVIDER=off` to disable cross-checking

**Categories not processed**
- Ensure category names in `QBIT_ALLOWED_CATEGORIES` exactly match qBittorrent categories
- Categories are normalized to lowercase for comparison
- Check qBittorrent logs to verify script is being called with correct parameters

### Debug Mode

Enable detailed logging:
```bash
LOG_LEVEL=DEBUG
```

This will show:
- HTTP request/response details
- Sonarr/Radarr API communication  
- File analysis decisions
- Whitelist matching logic
- Metadata fetch progress

### Health Checks

Monitor these indicators:
- ✅ `qB: login OK` - Authentication successful
- ✅ `Started torrent ... after checks` - Normal allow path
- ⚠️ `Pre-air: BLOCK` - Expected blocking behavior  
- ❌ `Unhandled error` - Configuration or connectivity issue

---
