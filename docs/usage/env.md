# Environment Variables Reference

Complete reference of all environment variables supported by qbit-guard, organized by feature area.

---

## Essential qBittorrent Connection

| Variable | Default | Description |
|----------|---------|-------------|
| `QBIT_HOST` | - | **Required.** qBittorrent WebUI URL (e.g., `http://qbittorrent:8080`) |
| `QBIT_USER` | `admin` | qBittorrent WebUI username |
| `QBIT_PASS` | - | **Required.** qBittorrent WebUI password |
| `QBIT_ALLOWED_CATEGORIES` | - | **Required.** Comma-separated list of categories to process |
| `QBIT_DELETE_FILES` | `true` | Delete files when removing torrents |
| `QBIT_IGNORE_TLS` | `0` | Set to `1` to ignore SSL certificate errors |
| `QBIT_DRY_RUN` | `0` | Set to `1` for testing mode (no actual deletions) |

---

## Container Watcher (Polling Mode)

| Variable | Default | Description |
|----------|---------|-------------|
| `WATCH_POLL_SECONDS` | `3.0` | How often to check qBittorrent for new torrents (seconds) |
| `WATCH_PROCESS_EXISTING_AT_START` | `0` | Process existing torrents when container starts (`0` or `1`) |
| `WATCH_RESCAN_KEYWORD` | `rescan` | Keyword in category/tags to force reprocessing |

---

## Sonarr Integration (Pre-air Gate)

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_PREAIR_CHECK` | `0` | Enable pre-air checking (`0` or `1`) |
| `SONARR_URL` | - | Sonarr base URL (e.g., `http://sonarr:8989`) |
| `SONARR_APIKEY` | - | Sonarr API key |
| `SONARR_CATEGORIES` | `tv-sonarr` | Categories to apply pre-air checks to |
| `EARLY_GRACE_HOURS` | `6` | Allow releases this many hours before air date |
| `EARLY_HARD_LIMIT_HOURS` | `72` | Block releases more than this many hours early |
| `WHITELIST_OVERRIDES_HARD_LIMIT` | `0` | Let whitelisted releases bypass hard limit (`0` or `1`) |
| `EARLY_WHITELIST_GROUPS` | - | Comma-separated list of trusted release groups |
| `EARLY_WHITELIST_INDEXERS` | - | Comma-separated list of trusted indexers |
| `EARLY_WHITELIST_TRACKERS` | - | Comma-separated list of trusted trackers |
| `RESUME_IF_NO_HISTORY` | `1` | Proceed if Sonarr history not found (`0` or `1`) |
| `SONARR_TIMEOUT_SEC` | `45` | HTTP timeout for Sonarr API calls |
| `SONARR_RETRIES` | `3` | Retry attempts for Sonarr operations |

---

## Radarr Integration

| Variable | Default | Description |
|----------|---------|-------------|
| `RADARR_URL` | - | Radarr base URL (e.g., `http://radarr:7878`) |
| `RADARR_APIKEY` | - | Radarr API key |
| `RADARR_CATEGORIES` | `radarr` | Categories to apply Radarr blocklisting to |
| `RADARR_TIMEOUT_SEC` | `45` | HTTP timeout for Radarr API calls |
| `RADARR_RETRIES` | `3` | Retry attempts for Radarr operations |

---

## Internet Cross-Verification

| Variable | Default | Description |
|----------|---------|-------------|
| `INTERNET_CHECK_PROVIDER` | `off` | Provider selection: `off`, `tvmaze`, `tvdb`, or `both` |

### TVmaze Settings
| Variable | Default | Description |
|----------|---------|-------------|
| `TVMAZE_BASE` | `https://api.tvmaze.com` | TVmaze API base URL |
| `TVMAZE_TIMEOUT_SEC` | `8` | HTTP timeout for TVmaze API calls |

### TheTVDB Settings
| Variable | Default | Description |
|----------|---------|-------------|
| `TVDB_BASE` | `https://api4.thetvdb.com/v4` | TheTVDB API base URL |
| `TVDB_APIKEY` | - | TheTVDB API key (required for TVDB) |
| `TVDB_PIN` | - | TheTVDB PIN (optional) |
| `TVDB_LANGUAGE` | `eng` | Language code for TheTVDB |
| `TVDB_ORDER` | `default` | Episode order: `default` or `official` |
| `TVDB_TIMEOUT_SEC` | `8` | HTTP timeout for TheTVDB API calls |
| `TVDB_BEARER` | - | Reuse existing bearer token (optional) |

---

## ISO/BDMV Cleanup

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_ISO_CHECK` | `0` | Enable ISO/disc image cleanup (`0` or `1`) |
| `MIN_KEEPABLE_VIDEO_MB` | `50` | Minimum size for video files to keep (MB) |
| `METADATA_POLL_INTERVAL` | `1.5` | Seconds between file list checks during metadata fetching |
| `METADATA_MAX_WAIT_SEC` | `0` | Max wait for metadata resolution (`0` = infinite) |
| `METADATA_DOWNLOAD_BUDGET_BYTES` | `0` | Max bytes to download during metadata wait (`0` = no limit) |

---

## Extension Policy

| Variable | Default | Description |
|----------|---------|-------------|
| `GUARD_EXT_STRATEGY` | `block` | Extension strategy: `block` or `allow` |
| `GUARD_ALLOWED_EXTS` | - | Comma-separated list of allowed extensions (for `allow` mode) |
| `GUARD_BLOCKED_EXTS` | - | Comma-separated list of blocked extensions (overrides defaults in `block` mode) |
| `GUARD_EXT_DELETE_IF_ALL_BLOCKED` | `1` | Delete only if all files are disallowed (`0` or `1`) |
| `GUARD_EXT_DELETE_IF_ANY_BLOCKED` | `0` | Delete if any file is disallowed (`0` or `1`) |
| `GUARD_EXT_VIOLATION_TAG` | `trash:ext` | Tag applied to torrents deleted for extension violations |
| `GUARD_DISC_EXTS` | `iso,img,mdf,nrg,cue,bin` | Disc image extensions |
| `GUARD_EXTS_FILE` | - | Path to JSON config file (optional) |

---

## Logging and Performance

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging verbosity: `INFO` or `DEBUG` |
| `USER_AGENT` | `qbit-guard/2.0` | HTTP User-Agent string for API calls |

---

## Configuration by Use Case

### Minimal Setup
```bash
# Required minimum
QBIT_HOST=http://qbittorrent:8080
QBIT_USER=admin
QBIT_PASS=your_password
QBIT_ALLOWED_CATEGORIES=tv-sonarr,radarr

# Basic ISO cleanup
ENABLE_ISO_CHECK=1
```

### Pre-air Gate Only
```bash
# qBittorrent connection
QBIT_HOST=http://qbittorrent:8080
QBIT_USER=admin
QBIT_PASS=your_password
QBIT_ALLOWED_CATEGORIES=tv-sonarr

# Sonarr pre-air checking
ENABLE_PREAIR_CHECK=1
SONARR_URL=http://sonarr:8989
SONARR_APIKEY=your_sonarr_api_key
SONARR_CATEGORIES=tv-sonarr
EARLY_GRACE_HOURS=6
EARLY_HARD_LIMIT_HOURS=72
```

### Full Featured Setup
```bash
# qBittorrent
QBIT_HOST=http://qbittorrent:8080
QBIT_USER=admin
QBIT_PASS=your_password
QBIT_ALLOWED_CATEGORIES=tv-sonarr,radarr

# Pre-air checking
ENABLE_PREAIR_CHECK=1
SONARR_URL=http://sonarr:8989
SONARR_APIKEY=your_sonarr_api_key
EARLY_GRACE_HOURS=6
EARLY_HARD_LIMIT_HOURS=72
EARLY_WHITELIST_GROUPS=trusted_group1,trusted_group2

# Internet verification
INTERNET_CHECK_PROVIDER=tvmaze

# ISO cleanup
ENABLE_ISO_CHECK=1
MIN_KEEPABLE_VIDEO_MB=100

# Radarr integration
RADARR_URL=http://radarr:7878
RADARR_APIKEY=your_radarr_api_key

# Debugging
LOG_LEVEL=DEBUG
```

### High Performance Setup
```bash
# Faster polling
WATCH_POLL_SECONDS=1.0

# Increased timeouts for slow networks
SONARR_TIMEOUT_SEC=90
RADARR_TIMEOUT_SEC=90
TVMAZE_TIMEOUT_SEC=15

# Process existing torrents on startup
WATCH_PROCESS_EXISTING_AT_START=1

# Metadata limits for large torrents
METADATA_MAX_WAIT_SEC=300
METADATA_DOWNLOAD_BUDGET_BYTES=104857600  # 100MB
```

---

## Default Values Summary

Variables with meaningful defaults that you may not need to set:

| Variable | Default | Notes |
|----------|---------|-------|
| `QBIT_USER` | `admin` | Most qBittorrent installations |
| `QBIT_DELETE_FILES` | `true` | Usually desired behavior |
| `WATCH_POLL_SECONDS` | `3.0` | Good balance of responsiveness/resources |
| `EARLY_GRACE_HOURS` | `6` | Reasonable pre-air grace period |
| `EARLY_HARD_LIMIT_HOURS` | `72` | Prevents very early releases |
| `MIN_KEEPABLE_VIDEO_MB` | `50` | Filters out samples and extras |
| `LOG_LEVEL` | `INFO` | Change to `DEBUG` for troubleshooting |

---

## Next Steps

- **[Configuration Guide →](configure.md)** - Detailed setup instructions
- **[Examples →](../examples.md)** - Working configurations
- **[Troubleshooting →](../troubleshooting.md)** - Common variable issues
