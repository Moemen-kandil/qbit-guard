# Configuration Examples

This page provides working examples of qbit-guard configurations for different deployment scenarios and use cases.

---

## Docker Compose Examples

### Minimal Configuration

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
      - sonarr

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

### Full Configuration

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

### Legacy Script Mode (Reference)

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

---

## Kubernetes Examples

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: qbit-guard-config
data:
  QBIT_HOST: "http://qbittorrent:8080"
  QBIT_USER: "admin"
  QBIT_ALLOWED_CATEGORIES: "tv-sonarr,radarr"
  ENABLE_PREAIR_CHECK: "1"
  SONARR_URL: "http://sonarr:8989"
  EARLY_GRACE_HOURS: "6"
  EARLY_HARD_LIMIT_HOURS: "72"
  INTERNET_CHECK_PROVIDER: "tvmaze"
  ENABLE_ISO_CHECK: "1"
  MIN_KEEPABLE_VIDEO_MB: "50"
  LOG_LEVEL: "INFO"
```

### Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: qbit-guard-secrets
type: Opaque
stringData:
  QBIT_PASS: "your_qbittorrent_password"
  SONARR_APIKEY: "your_sonarr_api_key"
  RADARR_APIKEY: "your_radarr_api_key"
  TVDB_APIKEY: "your_tvdb_api_key"
```

### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: qbit-guard
spec:
  replicas: 1
  selector:
    matchLabels:
      app: qbit-guard
  template:
    metadata:
      labels:
        app: qbit-guard
    spec:
      containers:
      - name: qbit-guard
        image: ghcr.io/gengines/qbit-guard:1.0.0
        envFrom:
        - configMapRef:
            name: qbit-guard-config
        - secretRef:
            name: qbit-guard-secrets
        resources:
          limits:
            memory: "512Mi"
            cpu: "500m"
          requests:
            memory: "128Mi"
            cpu: "100m"
        livenessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - "ps aux | grep -v grep | grep python"
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          exec:
            command:
            - /bin/sh
            - -c
            - "ps aux | grep -v grep | grep python"
          initialDelaySeconds: 5
          periodSeconds: 10
      restartPolicy: Always
```

---

## Use Case Examples

### TV Shows Only (Sonarr)

```yaml
environment:
  - QBIT_HOST=http://qbittorrent:8080
  - QBIT_USER=admin
  - QBIT_PASS=your_password
  - QBIT_ALLOWED_CATEGORIES=tv-sonarr
  
  # Pre-air checking
  - ENABLE_PREAIR_CHECK=1
  - SONARR_URL=http://sonarr:8989
  - SONARR_APIKEY=your_api_key
  - EARLY_GRACE_HOURS=6
  - EARLY_HARD_LIMIT_HOURS=72
  
  # Strict release group whitelist
  - EARLY_WHITELIST_GROUPS=scene_group1,scene_group2,trusted_p2p
  - WHITELIST_OVERRIDES_HARD_LIMIT=1
  
  # Internet cross-verification
  - INTERNET_CHECK_PROVIDER=tvmaze
  
  - LOG_LEVEL=INFO
```

### Movies Only (Radarr)

```yaml
environment:
  - QBIT_HOST=http://qbittorrent:8080
  - QBIT_USER=admin
  - QBIT_PASS=your_password
  - QBIT_ALLOWED_CATEGORIES=radarr
  
  # ISO cleanup for movies
  - ENABLE_ISO_CHECK=1
  - MIN_KEEPABLE_VIDEO_MB=100  # Higher threshold for movies
  
  # Radarr integration
  - RADARR_URL=http://radarr:7878
  - RADARR_APIKEY=your_radarr_api_key
  
  # Aggressive metadata fetching
  - METADATA_MAX_WAIT_SEC=600  # 10 minutes for large files
  - METADATA_DOWNLOAD_BUDGET_BYTES=209715200  # 200MB
  
  - LOG_LEVEL=INFO
```

### High Performance Setup

```yaml
environment:
  # Faster polling
  - WATCH_POLL_SECONDS=1.0
  
  # Process existing on startup
  - WATCH_PROCESS_EXISTING_AT_START=1
  
  # Aggressive timeouts
  - SONARR_TIMEOUT_SEC=90
  - RADARR_TIMEOUT_SEC=90
  - TVMAZE_TIMEOUT_SEC=15
  - TVDB_TIMEOUT_SEC=15
  
  # More retries
  - SONARR_RETRIES=5
  - RADARR_RETRIES=5
  
  # Debug logging for monitoring
  - LOG_LEVEL=DEBUG
```

### Strict Extension Policy

```yaml
environment:
  # Allow strategy - only specified extensions
  - GUARD_EXT_STRATEGY=allow
  - GUARD_ALLOWED_EXTS=mkv,mp4,m4v,webm,srt,ass,flac,aac
  
  # Delete if ANY disallowed file found
  - GUARD_EXT_DELETE_IF_ANY_BLOCKED=1
  
  # Custom violation tag
  - GUARD_EXT_VIOLATION_TAG=deleted:extension
```

### Testing and Development

```yaml
environment:
  # Dry run - no actual deletions
  - QBIT_DRY_RUN=1
  
  # Debug everything
  - LOG_LEVEL=DEBUG
  
  # Fast polling for testing
  - WATCH_POLL_SECONDS=1.0
  
  # Process existing torrents immediately
  - WATCH_PROCESS_EXISTING_AT_START=1
  
  # Short timeouts to fail fast during testing
  - SONARR_TIMEOUT_SEC=10
  - RADARR_TIMEOUT_SEC=10
  
  # Minimal metadata wait
  - METADATA_MAX_WAIT_SEC=30
```

---

## Integration Patterns

### Behind Reverse Proxy

When running behind a reverse proxy, use direct service URLs for API calls:

```yaml
environment:
  # Use internal service URLs, not proxy URLs
  - QBIT_HOST=http://qbittorrent:8080  # NOT https://your-domain.com/qbittorrent
  - SONARR_URL=http://sonarr:8989      # NOT https://your-domain.com/sonarr
  - RADARR_URL=http://radarr:7878      # NOT https://your-domain.com/radarr
  
  # Increase timeouts if proxy adds latency
  - SONARR_TIMEOUT_SEC=60
  - RADARR_TIMEOUT_SEC=60
```

### Multiple qBittorrent Instances

Run separate qbit-guard instances for different qBittorrent servers:

```yaml
services:
  qbit-guard-main:
    image: ghcr.io/gengines/qbit-guard:1.0.0
    environment:
      - QBIT_HOST=http://qbittorrent-main:8080
      - QBIT_ALLOWED_CATEGORIES=tv-sonarr,radarr
      # ... other config

  qbit-guard-4k:
    image: ghcr.io/gengines/qbit-guard:1.0.0
    environment:
      - QBIT_HOST=http://qbittorrent-4k:8080
      - QBIT_ALLOWED_CATEGORIES=tv-4k,movies-4k
      # ... other config
```

### External Services

Connect to external Sonarr/Radarr instances:

```yaml
environment:
  - SONARR_URL=https://external-sonarr.example.com
  - RADARR_URL=https://external-radarr.example.com
  
  # May need longer timeouts for internet connections
  - SONARR_TIMEOUT_SEC=120
  - RADARR_TIMEOUT_SEC=120
  
  # Internet verification still works
  - INTERNET_CHECK_PROVIDER=tvmaze
```

---

## Real-world Use Cases

### Home Media Server

```yaml
# Family-friendly setup with reasonable restrictions
environment:
  - QBIT_ALLOWED_CATEGORIES=tv-sonarr,radarr,books
  - ENABLE_PREAIR_CHECK=1
  - EARLY_GRACE_HOURS=12      # More lenient for family use
  - EARLY_HARD_LIMIT_HOURS=168  # 1 week limit
  - ENABLE_ISO_CHECK=1
  - MIN_KEEPABLE_VIDEO_MB=25  # Keep smaller files for kids content
  - LOG_LEVEL=INFO
```

### Power User Setup

```yaml
# Aggressive configuration for experienced users
environment:
  - EARLY_GRACE_HOURS=1       # Very strict pre-air
  - EARLY_HARD_LIMIT_HOURS=48  # 2 day hard limit
  - EARLY_WHITELIST_GROUPS=scene1,scene2,trusted_internal
  - WHITELIST_OVERRIDES_HARD_LIMIT=1
  - INTERNET_CHECK_PROVIDER=both  # Cross-verify with both APIs
  - MIN_KEEPABLE_VIDEO_MB=100     # Aggressive size filtering
  - GUARD_EXT_STRATEGY=allow      # Whitelist approach
  - GUARD_EXT_DELETE_IF_ANY_BLOCKED=1  # Strict enforcement
```

### Seedbox/VPS Deployment

```yaml
# Optimized for remote/VPS deployment
environment:
  - WATCH_POLL_SECONDS=5.0    # Less frequent polling for limited resources
  - SONARR_TIMEOUT_SEC=120    # Longer timeouts for internet latency
  - RADARR_TIMEOUT_SEC=120
  - METADATA_MAX_WAIT_SEC=180  # Conservative metadata timeout
  - METADATA_DOWNLOAD_BUDGET_BYTES=52428800  # 50MB limit for bandwidth
  - LOG_LEVEL=INFO  # Reduce log verbosity
```

---

## Next Steps

- **[Installation Guide →](usage/install.md)** - Set up your chosen configuration
- **[Configuration Guide →](usage/configure.md)** - Customize for your needs
- **[Troubleshooting →](troubleshooting.md)** - Fix common issues
- **[Environment Variables →](usage/env.md)** - Complete variable reference