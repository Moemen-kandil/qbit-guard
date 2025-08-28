# Installation Guide

qbit-guard can be deployed in two ways: as a **containerized service** (recommended) or as a **traditional script**. Choose the method that best fits your setup.

---

## Docker Installation (Recommended)

The containerized version runs as a standalone service that continuously monitors qBittorrent, eliminating the need for webhook configuration.

### Prerequisites

- **Docker** and **Docker Compose** installed
- **qBittorrent** accessible over the network
- **Sonarr/Radarr** accessible over the network (optional but recommended)
- Network connectivity between all services

### Quick Start

1. **Pull the official image**:
   ```bash
   docker pull ghcr.io/gengines/qbit-guard:latest
   ```

2. **Create a basic docker-compose.yml**:
   ```yaml
   version: '3.8'
   services:
     qbit-guard:
       image: ghcr.io/gengines/qbit-guard:latest
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

### Container Modes

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

### Network Requirements

qbit-guard needs network connectivity to your services:

- **qBittorrent API**: HTTP access to qBittorrent's Web UI (default port 8080)
- **Sonarr API**: HTTP access to Sonarr (default port 8989)
- **Radarr API**: HTTP access to Radarr (default port 7878)  
- **Internet APIs**: HTTPS access to TVmaze and TheTVDB for cross-verification

#### Docker Compose Networking

Create a shared network for all services:

```yaml
networks:
  arr-network:
    driver: bridge
```

All services (qbit-guard, qbittorrent, sonarr, radarr) should use the same network to enable service discovery by container name.

---

## Script Installation (Traditional)

For users who prefer the traditional webhook approach or need to customize the deployment:

### Prerequisites

- **Python 3.8+** installed
- **qBittorrent** with WebUI enabled
- **Sonarr/Radarr** accessible (optional)

### Installation Steps

1. **Download and make executable**:
   ```bash
   curl -o /config/scripts/qbit-guard.py https://raw.githubusercontent.com/GEngines/qbit-guard/main/src/guard.py
   chmod +x /config/scripts/qbit-guard.py
   ```

2. **Configure qBittorrent**:
   - Navigate to **Options** → **Downloads** → **Run external program**
   - **Run on torrent added**:
     ```bash
     /usr/bin/python3 /config/scripts/qbit-guard.py %I %L
     ```
   - **Important**: Remove any existing "Run on torrent added" scripts to avoid conflicts

3. **Set environment variables** in your container/docker-compose file

4. **Restart qBittorrent**

### Script Mode vs Container Mode

| Feature | Container Mode | Script Mode |
|---------|---------------|-------------|
| **Setup Complexity** | Simple | Moderate |
| **Webhook Required** | No | Yes |
| **Continuous Monitoring** | Yes | Per-torrent |
| **Container Restarts** | Graceful | Manual reconfig |
| **Resource Usage** | Single process | Per-execution |
| **Debugging** | Centralized logs | Per-execution logs |
| **Recommended For** | Most users | Advanced setups |

---

## Next Steps

After installation, proceed to:

- **[Configuration Guide →](configure.md)** - Configure qBittorrent integration, Sonarr/Radarr, and other features
- **[Environment Variables →](env.md)** - Complete reference of all configuration options
- **[Examples →](../examples.md)** - Working Docker Compose and Kubernetes examples

> **Tip**: A complete working `docker-compose.yml` file is included in the repository root with all configuration options documented.
