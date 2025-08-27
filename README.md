# qbit-guard

A zero-dependency Python guard for qBittorrent that provides intelligent torrent management with pre-air checking and ISO/BDMV cleanup.

## Features

- **Pre-air gate (Sonarr)**: Stops new TV torrents, checks airDateUtc, optional TVmaze/TheTVDB cross-check, and only allows legitimate early drops using grace/whitelist/hard-cap rules
- **ISO/BDMV cleaner**: After metadata arrives, removes disc-image-only/non-importable torrents
- **Smart blocklisting**: Blocklists in Sonarr/Radarr before deletion, using deduped history (single "grabbed" record) with queue failover if the history endpoint times out
- **Version compatibility**: Works with qBittorrent 5.x (start/stop) and 4.x fallback (resume/pause)
- **Zero dependencies**: No external libraries, just Python 3 stdlib
- **Container-friendly**: Logs to stdout for container environments

## How it Works

### Workflow Overview

1. **On add**: Torrent is stopped and tagged (`guard:stopped`)

2. **Pre-air gate**: If category matches a Sonarr category:
   - ✅ Allow if aired, or within grace window, or passes whitelist (group/indexer/tracker), unless hard cap exceeded
   - ❌ If blocked: blocklist in Sonarr (history → queue failover) and delete in qBittorrent
   - 🔄 If allowed: torrent is started briefly to fetch metadata (waits until `/torrents/files` is non-empty), then stopped

3. **ISO/BDMV check**: If only ISO/BDMV and no keepable video → blocklist in Sonarr/Radarr and delete

4. **Final step**: Otherwise torrent is started and tagged (`guard:allowed`)

## Requirements

- qBittorrent 5.x (4.x supported via fallback)
- Python 3.8+ inside your container/host
- Sonarr/Radarr (optional but recommended for blocklisting)
- Network reachability between qBittorrent ↔ Sonarr/Radarr
- No third-party Python packages needed

## Installation

1. **Save the script** (e.g., `/config/scripts/qbit-guard.py`) and make it executable:
   ```bash
   chmod +x /config/scripts/qbit-guard.py
   ```

2. **Configure qBittorrent**:
   - Go to **Options** → **Downloads** → **Run external program**
   - Set **Run on torrent added**:
     ```bash
     /usr/bin/python3 /config/scripts/qbit-guard.py %I %L
     ```

3. **Set environment variables** (see configuration below)

4. **Restart qBittorrent** if needed

## Configuration

All settings are configured via environment variables with sensible defaults.

### Minimum Required Configuration

```bash
# qBittorrent
QBIT_HOST=http://qbittorrent:8080
QBIT_USER=admin
QBIT_PASS=adminadmin
QBIT_ALLOWED_CATEGORIES="tv-sonarr,radarr"
QBIT_DELETE_FILES=true

# Sonarr (pre-air gate + blocklist)
ENABLE_PREAIR_CHECK=1
SONARR_URL=http://sonarr:8989
SONARR_APIKEY=your_sonarr_api_key_here
SONARR_CATEGORIES="tv-sonarr"

# Radarr (ISO/BDMV deletes -> blocklist)
RADARR_URL=http://radarr:7878
RADARR_APIKEY=your_radarr_api_key_here
RADARR_CATEGORIES="radarr"
```

### Pre-air Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `EARLY_GRACE_HOURS` | 6 | Allow small early airs within this window |
| `EARLY_HARD_LIMIT_HOURS` | 72 | Block if too early unless whitelisted |
| `EARLY_WHITELIST_GROUPS` | - | Comma-separated, case-insensitive group names |
| `EARLY_WHITELIST_INDEXERS` | - | Comma-separated, case-insensitive indexer names |
| `EARLY_WHITELIST_TRACKERS` | - | Comma-separated, case-insensitive tracker names |
| `WHITELIST_OVERRIDES_HARD_LIMIT` | 0 | Set to 1 to let whitelist bypass hard cap |
| `RESUME_IF_NO_HISTORY` | 1 | Proceed if Sonarr history isn't found yet |

### Internet Cross-check (Optional)

| Variable | Default | Description |
|----------|---------|-------------|
| `INTERNET_CHECK_PROVIDER` | `tvmaze` | `off`, `tvmaze`, `tvdb`, or `both` |
| `TVDB_APIKEY` | - | Required if using TVDB |
| `TVDB_PIN` | - | Optional TVDB PIN |

### ISO/Metadata Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_ISO_CHECK` | - | Set to 1 to enable ISO/BDMV cleanup |
| `MIN_KEEPABLE_VIDEO_MB` | 50 | Minimum video file size to keep |
| `METADATA_POLL_INTERVAL` | 1.5 | Seconds between metadata checks |
| `METADATA_MAX_WAIT_SEC` | 0 | 0 = wait indefinitely for metadata |
| `METADATA_DOWNLOAD_BUDGET_BYTES` | 0 | Optional payload cap while waiting |

### Reliability & Logging

| Variable | Default | Description |
|----------|---------|-------------|
| `SONARR_TIMEOUT_SEC` | 45 | Sonarr API timeout |
| `SONARR_RETRIES` | 3 | Sonarr API retry attempts |
| `RADARR_TIMEOUT_SEC` | 45 | Radarr API timeout |
| `RADARR_RETRIES` | 3 | Radarr API retry attempts |
| `LOG_LEVEL` | `INFO` | Logging level (`INFO` or `DEBUG`) |

## Usage

1. **Configure environment variables** (Docker env / Docker Compose / Kubernetes)
2. **Ensure only this script runs** on torrent added (remove legacy hooks)
3. **Add torrents to allowed categories** (e.g., `tv-sonarr`, `radarr`)
4. **Monitor container logs** for decisions: pre-air allow/block, ISO cleaner, blocklist via history/queue, etc.

## Important Notes

- **No duplicate blocklists**: The script only fails one "grabbed" record per unique release title
- **Queue failover**: If `/history/failed/{id}` times out, it calls `DELETE /queue/{id}?blocklist=true`
- **Magnet support**: Works with magnets (waits for metadata), and stops fast once the file list appears
- **Pure stdlib**: No `requests` or extra dependencies required

## Troubleshooting

### Common Issues

**Timeout blocklisting**
- Increase `SONARR_TIMEOUT_SEC` / `RADARR_TIMEOUT_SEC`
- Ensure you're hitting the LAN URL (avoid reverse-proxy timeouts)

**No Sonarr history yet**
- Set `RESUME_IF_NO_HISTORY=1` (default) to proceed to file checks

**Metadata loading slowly**
- Set `METADATA_MAX_WAIT_SEC=0` (infinite wait)
- Or reduce `METADATA_POLL_INTERVAL` (e.g., `0.5`)

### Debug Mode

Set `LOG_LEVEL=DEBUG` for verbose logging to troubleshoot issues.

---

**License**: [Add your license here]  
**Contributing**: [Add contribution guidelines here]  
**Issues**: [Link to issue tracker]
