# MT Server Setup Guide

## Quick Access

```bash
# From broklein, attach to mt work session:
tmux attach -t mt-epstein

# Or SSH directly:
ssh mt
cd /srv/epstein/epstein-archive
```

---

## Server Specs (mt)

**Verified:**
- **Storage:** 700GB dedicated LV at /srv/epstein ✅
- **Filesystem:** ext4 ✅
- **User:** mt ✅
- **Project:** /srv/epstein/epstein-archive ✅

**To verify:**
```bash
ssh mt "free -h"          # RAM
ssh mt "nproc"            # CPU cores
ssh mt "df -h /srv/epstein"  # Storage
```

---

## Initial Setup Complete

1. ✅ Cloned The-Stein-Files from GitHub
2. ✅ Removed .git history
3. ✅ Initialized fresh repo
4. ✅ Set git config (kleinpanic)
5. ✅ Initial commit

---

## Development Workflow

### Using tmux Session

```bash
# Attach to dedicated mt session
tmux attach -t mt-epstein

# Inside tmux:
# - Window 0: SSH to mt
# - Can split panes: Ctrl+b %  (vertical) or Ctrl+b "  (horizontal)
# - Detach: Ctrl+b d
```

### Direct SSH Commands

```bash
# Run commands on mt from broklein:
ssh mt "cd /srv/epstein/epstein-archive && <command>"

# Copy files to mt:
scp <file> mt:/srv/epstein/epstein-archive/

# Copy from mt:
scp mt:/srv/epstein/epstein-archive/<file> .
```

---

## Next Steps

### 1. Domain Decision (KLEIN)
Choose one:
- **Dedicated:** `epsteinlibrary.org` (recommended) - ~$12/year
- **Subdomain:** `archive.kleinpanic.com` - $0, uses existing domain

### 2. Install Production Stack (DEV)
```bash
ssh mt

# Update system
sudo apt update && sudo apt upgrade -y

# Install core dependencies
sudo apt install -y \
  postgresql-15 \
  nginx \
  python3.11 \
  python3-pip \
  python3-venv \
  git \
  curl \
  wget

# Install MeiliSearch
curl -L https://install.meilisearch.com | sh
sudo mv meilisearch /usr/local/bin/
sudo systemctl enable --now meilisearch

# Install Caddy (alternative to nginx if preferred)
# sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
# curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
# curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
# sudo apt update && sudo apt install caddy
```

### 3. Configure PostgreSQL
```bash
sudo -u postgres psql

CREATE DATABASE epstein_archive;
CREATE USER epstein WITH PASSWORD '<secure-password>';
GRANT ALL PRIVILEGES ON DATABASE epstein_archive TO epstein;
\q
```

### 4. Python Environment
```bash
cd /srv/epstein/epstein-archive
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. edge-gateway HAProxy Config (KLEIN)

Example config for `/etc/haproxy/haproxy.cfg`:

```haproxy
frontend https_front
    bind *:443 ssl crt /etc/ssl/private/epsteinlibrary.pem
    default_backend epstein_backend

backend epstein_backend
    # mt via WireGuard
    server mt 10.8.0.2:8080 check
    
    # Rate limiting
    stick-table type ip size 100k expire 30s store http_req_rate(10s)
    http-request track-sc0 src
    http-request deny if { sc_http_req_rate(0) gt 100 }
    
    # Compression
    compression algo gzip
    compression type text/html text/plain text/css application/javascript application/json
```

### 6. Caddy Config on mt (Alternative to nginx)

```caddyfile
# /etc/caddy/Caddyfile
:8080 {
    root * /srv/epstein/epstein-archive/dist
    file_server
    
    # Reverse proxy for MeiliSearch
    reverse_proxy /api/search/* localhost:7700
    
    # Serve PDFs with proper headers
    @pdfs path *.pdf
    header @pdfs {
        Content-Type application/pdf
        Content-Disposition inline
        Cache-Control "public, max-age=31536000"
    }
    
    # Gzip compression
    encode gzip
    
    # Logs
    log {
        output file /var/log/caddy/access.log
        format json
    }
}
```

---

## Monitoring & Maintenance

### Disk Space
```bash
# Check storage usage
df -h /srv/epstein

# Check largest directories
du -h --max-depth=2 /srv/epstein | sort -hr | head -20
```

### Services
```bash
# Check service status
sudo systemctl status postgresql
sudo systemctl status meilisearch
sudo systemctl status caddy  # or nginx

# View logs
sudo journalctl -u meilisearch -f
sudo journalctl -u caddy -f
tail -f /var/log/caddy/access.log
```

### Database
```bash
# Connect to database
psql -U epstein -d epstein_archive

# Check table sizes
\dt+

# Backup
pg_dump -U epstein epstein_archive > /srv/epstein/backups/db-$(date +%Y%m%d).sql
```

---

## Security Checklist

- [ ] Configure firewall (ufw) to only allow WireGuard + SSH
- [ ] Set up fail2ban for SSH protection
- [ ] Regular security updates: `sudo apt update && sudo apt upgrade`
- [ ] Database backups automated (daily cron)
- [ ] PDF backups via rsync or torrent seeding
- [ ] Monitoring/alerting for disk space
- [ ] HAProxy rate limiting configured
- [ ] SSL/TLS certificates configured (Let's Encrypt)

---

## Development Commands

### Ingestion
```bash
cd /srv/epstein/epstein-archive
source venv/bin/activate
python -m scripts.ingest_enumerate --datasets 1-5 --test
```

### Building Site
```bash
make extract   # Extract metadata from PDFs
make build     # Build static site
```

### Search Indexing
```bash
python -m scripts.index_search  # Push to MeiliSearch
```

### Database Operations
```bash
python -m scripts.import_metadata  # Import to PostgreSQL
python -m scripts.extract_people   # People/relationship extraction
```

---

## Tmux Cheatsheet

```bash
# Sessions
tmux attach -t mt-epstein    # Attach to session
Ctrl+b d                     # Detach from session
tmux ls                      # List sessions
tmux kill-session -t <name>  # Kill session

# Panes
Ctrl+b %    # Split vertically
Ctrl+b "    # Split horizontally
Ctrl+b o    # Switch panes
Ctrl+b x    # Kill pane

# Windows
Ctrl+b c    # Create new window
Ctrl+b n    # Next window
Ctrl+b p    # Previous window
Ctrl+b 0-9  # Switch to window number
```

---

## Git Workflow

### On mt
```bash
cd /srv/epstein/epstein-archive

# Stage changes
git add <files>

# Commit
git commit -m "feat: <description>"

# Push to new GitHub repo (after creating it)
git remote add origin git@github.com:kleinpanic/epstein-archive-production.git
git push -u origin main
```

### On broklein (original)
```bash
cd ~/codeWS/Projects/Eppie

# This repo stays as-is (prototype/research)
# No changes needed
```

---

## Troubleshooting

### SSH Connection Issues
```bash
# Test connection
ssh -v mt

# Check WireGuard
sudo wg show
ping 10.8.0.2  # mt IP on WireGuard
```

### Permission Issues
```bash
# Fix ownership
sudo chown -R mt:mt /srv/epstein/epstein-archive

# Check file permissions
ls -la /srv/epstein/epstein-archive
```

### Service Won't Start
```bash
# Check logs
sudo journalctl -xe

# Check ports
sudo ss -tlnp | grep <port>

# Restart service
sudo systemctl restart <service>
```

---

## Resources

- **mt specs:** (to be verified)
- **edge-gateway:** DigitalOcean VPS
- **WireGuard config:** Klein has this
- **Domain:** TBD (Klein deciding)
- **SSL cert:** Let's Encrypt (free, auto-renew)

Ready to build once domain is chosen!
