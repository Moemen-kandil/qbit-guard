# qbit-guard

A zero-dependency Python guard for qBittorrent that provides intelligent torrent management with **pre-air checking** and **ISO/BDMV cleanup**.

[Install →](usage/install.md) · [Configure →](usage/configure.md) · [Environment Vars →](usage/env.md) · [Development →](usage/dev.md)

---

## Features

- **Pre-air gate (Sonarr)**  
  Stops new TV torrents, checks `airDateUtc` with configurable grace/cap windows, supports release group / indexer / tracker whitelisting, and blocks too-early releases.

- **ISO/BDMV cleaner**  
  After metadata arrives, removes disc-image-only torrents (ISO/IMG/MDF/NRG/CUE/BIN files or `BDMV` / `VIDEO_TS` folders) that don’t contain keepable video.

- **Smart blocklisting**  
  Blocklists in Sonarr/Radarr before deletion using deduped history (single “grabbed” record per unique release), with queue failover if the history endpoint times out.

- **Optional internet cross-verification**  
  TVmaze and/or TheTVDB to cross-check Sonarr air dates.

- **qBittorrent 5.x & 4.x**  
  Uses start/stop with resume/pause fallback for 4.x.

- **Zero deps & container-friendly**  
  Pure Python 3.8+ stdlib; configured by environment variables; logs to stdout.

---

## How it works (flow)

1. **On add** → torrent immediately stopped and tagged `guard:stopped`.  
2. **Category filter** → only `QBIT_ALLOWED_CATEGORIES` are processed.  
3. **Pre-air gate** (if Sonarr category): consult Sonarr (+ optional TVmaze/TVDB).  
   - If **blocked** → blocklist in *arr, tag `trash:preair`, delete torrent.  
   - If **allowed** → continue.  
4. **Metadata fetch** → briefly start torrent to get file list (magnet-friendly), reannounce periodically, respect wait/budget limits, then stop.  
5. **ISO/BDMV cleanup** → if disc-image-only and no keepable video ≥ `MIN_KEEPABLE_VIDEO_MB`, blocklist + delete (tag `trash:iso`).  
6. **Start for real** → tag `guard:allowed` and start torrent.

**Keepable video**: `.mkv .mp4 .m4v .avi .ts .m2ts .mov .webm` (size ≥ threshold).

---

## Requirements

- **qBittorrent** 5.x preferred (4.x supported).
- **Python** 3.8+ (if running as a script).
- **Sonarr** v3 (optional; for pre-air).
- **Radarr** v3 (optional; used for ISO deletes).
- **Network** connectivity between qBittorrent and *arr.
- **No external Python deps**.

---

## Quick start (Docker Compose)

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
      - ENABLE_ISO_CHECK=1
      - LOG_LEVEL=INFO
    networks: [arr-network]

networks:
  arr-network: { driver: bridge }
