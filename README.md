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

## Usage Examples

### Docker Compose

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
