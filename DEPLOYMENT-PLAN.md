# KimiDokku MCP Deployment Plan

## Server Overview

**Server:** clawtech.ru (31.177.83.27)  
**Provider:** SpaceWeb VPS  
**SSH Port:** 2233  
**Current Apps:**
- `landing` - Main website (clawtech.ru)
- `docs-platform` - Documentation platform
- `hello-world` - Test application

**Server Resources:**
- **CPU:** 2 cores
- **Memory:** 3.9 GB (896 MB used, 3.0 GB available)
- **Disk:** 40 GB (13 GB used, 25 GB available)
- **OS:** Ubuntu 24.04 LTS
- **Dokku:** Installed and configured

---

## Deployment Strategy

### App Name
**Recommended:** `kimidokku`  
**Domain:** `kimidokku.clawtech.ru` (or `mcp.clawtech.ru`)

**Alternative names (if conflicts):**
- `kimidokku-mcp`
- `dokku-mcp`
- `mcp-platform`

---

## Pre-Deployment Checklist

### 1. Verify No Conflicts
```bash
# Check if app name exists
ssh -p 2233 root@clawtech.ru "dokku apps:exists kimidokku"

# Check if domain is available
ssh -p 2233 root@clawtech.ru "dokku domains:report kimidokku"
```

### 2. Required Environment Variables

KimiDokku MCP requires these environment variables:

```bash
# Required
KIMIDOKKU_DOMAIN="kimidokku.clawtech.ru"
AUTH_USER="admin"
AUTH_PASS="<GENERATE_STRONG_PASSWORD>"
WEBHOOK_SECRET="<GENERATE_WEBHOOK_SECRET>"

# Optional (with defaults)
DB_PATH="/app/data/kimidokku.db"
CSRF_SECRET="<GENERATE_CSRF_SECRET>"
RATE_LIMIT_STORAGE="memory"
```

**Generate secrets:**
```bash
# Generate strong passwords
openssl rand -base64 32  # For AUTH_PASS
openssl rand -hex 32     # For WEBHOOK_SECRET
openssl rand -hex 32     # For CSRF_SECRET
```

---

## Deployment Steps

### Option A: Git Push Deployment (Recommended)

#### Step 1: Prepare Repository
```bash
# From KimiDokku MCP project root
cd /Users/anrogdev/OpenWork/KimiDokku MCP

# Ensure all files are committed
git status

# Add Dokku remote
git remote add dokku dokku@clawtech.ru:kimidokku
```

#### Step 2: Create Procfile
Create `Procfile` in project root:
```
web: python -m kimidokku.main
```

#### Step 3: Create runtime.txt
```
python-3.13.0
```

#### Step 4: Configure Dokku App
```bash
# Create app on Dokku server
ssh -p 2233 root@clawtech.ru "dokku apps:create kimidokku"

# Set environment variables
ssh -p 2233 root@clawtech.ru "dokku config:set kimidokku KIMIDOKKU_DOMAIN=kimidokku.clawtech.ru"
ssh -p 2233 root@clawtech.ru "dokku config:set kimidokku AUTH_USER=admin"
ssh -p 2233 root@clawtech.ru "dokku config:set kimidokku AUTH_PASS=<GENERATED_PASSWORD>"
ssh -p 2233 root@clawtech.ru "dokku config:set kimidokku WEBHOOK_SECRET=<GENERATED_SECRET>"
ssh -p 2233 root@clawtech.ru "dokku config:set kimidokku CSRF_SECRET=<GENERATED_SECRET>"
ssh -p 2233 root@clawtech.ru "dokku config:set kimidokku DB_PATH=/app/data/kimidokku.db"
```

#### Step 5: Setup Persistent Storage
```bash
# Create storage directory
ssh -p 2233 root@clawtech.ru "dokku storage:ensure-directory kimidokku"

# Mount storage to container
ssh -p 2233 root@clawtech.ru "dokku storage:mount kimidokku /var/lib/dokku/data/storage/kimidokku:/app/data"
```

#### Step 6: Deploy
```bash
# Push to Dokku
git push dokku main

# Check deployment status
ssh -p 2233 root@clawtech.ru "dokku ps:report kimidokku"
```

#### Step 7: Configure Domain & SSL
```bash
# Set domain
ssh -p 2233 root@clawtech.ru "dokku domains:set kimidokku kimidokku.clawtech.ru"

# Enable SSL
ssh -p 2233 root@clawtech.ru "dokku letsencrypt:set kimidokku email admin@clawtech.ru"
ssh -p 2233 root@clawtech.ru "dokku letsencrypt:enable kimidokku"

# Check SSL status
ssh -p 2233 root@clawtech.ru "dokku letsencrypt:list"
```

---

### Option B: Docker Image Deployment

For more control over the build process:

#### Step 1: Create Dockerfile
```dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Install package
RUN pip install -e .

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "-m", "kimidokku.main"]
```

#### Step 2: Build and Deploy
```bash
# Build image locally
docker build -t kimidokku:latest .

# Tag for registry
docker tag kimidokku:latest registry.clawtech.ru/kimidokku:latest

# Push to registry
docker push registry.clawtech.ru/kimidokku:latest

# Deploy on server
ssh -p 2233 root@clawtech.ru "dokku git:from-image kimidokku registry.clawtech.ru/kimidokku:latest"
```

---

## Post-Deployment Verification

### 1. Check Application Status
```bash
# App status
ssh -p 2233 root@clawtech.ru "dokku ps:report kimidokku"

# App logs
ssh -p 2233 root@clawtech.ru "dokku logs kimidokku -t"
```

### 2. Test Endpoints
```bash
# Health check
curl https://kimidokku.clawtech.ru/health

# MCP endpoint (should require auth)
curl -I https://kimidokku.clawtech.ru/mcp

# Web UI
curl -u admin:<PASSWORD> https://kimidokku.clawtech.ru/
```

### 3. Verify Database
```bash
# Check database file exists
ssh -p 2233 root@clawtech.ru "ls -la /var/lib/dokku/data/storage/kimidokku/"

# Enter container and check
ssh -p 2233 root@clawtech.ru "dokku enter kimidokku"
ls -la /app/data/
sqlite3 /app/data/kimidokku.db ".tables"
```

---

## Potential Issues & Solutions

### Issue 1: Port Conflict
**Problem:** KimiDokku MCP runs on port 8000, but another app might use it.

**Solution:** Dokku handles port mapping automatically via nginx proxy. The app listens on its internal port, Dokku exposes it externally.

```bash
# Check port mapping
ssh -p 2233 root@clawtech.ru "dokku proxy:ports kimidokku"

# If needed, set specific port
ssh -p 2233 root@clawtech.ru "dokku proxy:ports-set kimidokku http:80:8000"
```

### Issue 2: Database Permissions
**Problem:** SQLite database not writable in container.

**Solution:** Ensure storage directory has correct permissions:
```bash
ssh -p 2233 root@clawtech.ru "chown -R 32767:32767 /var/lib/dokku/data/storage/kimidokku"
```

### Issue 3: Memory Constraints
**Problem:** Server has limited memory (3.9GB total).

**Solution:** Monitor memory usage and scale if needed:
```bash
# Check memory usage
ssh -p 2233 root@clawtech.ru "dokku resource:report kimidokku"

# Set memory limit (if needed)
ssh -p 2233 root@clawtech.ru "dokku resource:limit memory kimidokku 512M"
```

### Issue 4: SSL Certificate
**Problem:** Let's Encrypt rate limiting or DNS issues.

**Solution:** 
```bash
# Check SSL status
ssh -p 2233 root@clawtech.ru "dokku letsencrypt:report kimidokku"

# Re-enable if needed
ssh -p 2233 root@clawtech.ru "dokku letsencrypt:disable kimidokku"
ssh -p 2233 root@clawtech.ru "dokku letsencrypt:enable kimidokku"
```

---

## Security Considerations

### 1. Firewall Rules
KimiDokku MCP exposes:
- Port 80/443 (HTTP/HTTPS) via nginx
- Webhook endpoints at `/webhook/*`

**Action:** Ensure firewall allows web traffic:
```bash
# Check nftables
ssh -p 2233 root@clawtech.ru "nft list ruleset | grep 443"
```

### 2. Authentication
- Default auth: Basic HTTP Auth (admin/password)
- MCP endpoints: API key based
- Web UI: CSRF protected

**Action:** Change default password immediately after deployment!

### 3. Webhook Security
- GitHub: HMAC-SHA256 signature verification
- GitLab: Token-based verification

**Action:** Configure webhook secrets in GitHub/GitLab settings.

### 4. CrowdSec Integration
The server has CrowdSec installed. KimiDokku MCP's rate limiting adds additional protection.

---

## Monitoring Setup

### 1. Application Logs
```bash
# Stream logs
ssh -p 2233 root@clawtech.ru "dokku logs kimidokku -t"

# Recent logs
ssh -p 2233 root@clawtech.ru "dokku logs kimidokku -n 100"
```

### 2. Health Checks
Add to monitoring script (`scripts/cron/resource-monitor.sh`):
```bash
# Check KimiDokku MCP health
if ! curl -sf https://kimidokku.clawtech.ru/health > /dev/null; then
    echo "KimiDokku MCP health check failed" | logger
fi
```

### 3. Telegram Alerts
Update Telegram bot to monitor KimiDokku MCP.

---

## Rollback Plan

If deployment fails:

```bash
# Stop the app
ssh -p 2233 root@clawtech.ru "dokku ps:stop kimidokku"

# Or destroy completely
ssh -p 2233 root@clawtech.ru "dokku apps:destroy kimidokku"

# Check other apps are unaffected
ssh -p 2233 root@clawtech.ru "dokku apps:list"
```

---

## Summary

### What Will Be Affected

| Component | Impact | Action Required |
|-----------|--------|-----------------|
| **Dokku** | New app added | None |
| **Nginx** | New vhost added | Automatic |
| **SSL** | New certificate | Enable LetsEncrypt |
| **Storage** | New directory | Create storage mount |
| **Firewall** | No changes | Already allows 80/443 |
| **CrowdSec** | No changes | Works transparently |
| **Landing** | No impact | Separate app |
| **Docs Platform** | No impact | Separate app |

### Deployment Checklist

- [ ] App name confirmed (`kimidokku`)
- [ ] Domain configured (`kimidokku.clawtech.ru`)
- [ ] Environment variables set (AUTH_PASS, WEBHOOK_SECRET, etc.)
- [ ] Persistent storage mounted
- [ ] Git push successful
- [ ] SSL certificate enabled
- [ ] Health check passing
- [ ] Web UI accessible
- [ ] MCP endpoints working
- [ ] Webhooks configured (optional)

### Estimated Resources

- **Memory:** ~100-200MB (Python + FastAPI)
- **Disk:** ~100MB (app) + data growth
- **CPU:** Minimal at idle, moderate during deployments
- **Network:** HTTP/HTTPS traffic only

---

**Ready to Deploy?** Follow the steps in Option A (Git Push) for the simplest deployment.