# Install

qbit-guard can run as a **container service** (recommended) or as a **standalone script**.

- Configure options: see [configure.md](configure.md)  
- Full list of variables: see [env.md](env.md)

---

## Docker (recommended)

### Prerequisites
- Docker + Docker Compose
- qBittorrent, Sonarr/Radarr reachable over the network

### 1) Pull the image
```bash
docker pull ghcr.io/gengines/qbit-guard:1.0.0
