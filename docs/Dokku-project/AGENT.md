# KimiClaw Agent Guidelines

## ✅ CAN DO

- Read all documents in `/docs/Dokku-project/`
- Execute commands on VPS via SSH using key from `/keys/`
- Monitor logs, service status, metrics
- Create and send reports to Telegram
- Propose configuration changes (apply only after confirmation)
- Deploy applications via Dokku (git push)
- Restart services on failure
- Update CrowdSec collections
- Add new whitelist IPs (following procedure below)
- Deploy landing page (see Landing Deployment section)

## ❌ CANNOT DO

- Change root password or SSH keys
- Disable auditd, AIDE, or CrowdSec
- Modify CIS hardening policies
- Delete backups
- Expose private data (tokens, keys) in unsecured channels

## ⚠️ REQUIRES CONFIRMATION

- Change firewall rules
- Update system packages (apt upgrade)
- Modify Dokku configuration
- Add new SSH keys
- Remove or modify whitelist IPs (62.76.130.37, 43.98.167.164)

## 🔴 CRITICAL: Whitelist IP Management

When adding new IPs to whitelist:

1. **Add to Ansible vars:** Edit `ansible/group_vars/all/vars.yml`
2. **Update nftables:** Add to `whitelist_ips` list
3. **Update CrowdSec:** Already covered by same list
4. **Re-run Ansible:** `cd ansible && ansible-playbook site.yml`
5. **Verify:** 
   ```bash
   # Check nftables
   nft list set inet filter whitelist_ips
   
   # Check CrowdSec
   cscli decisions list -a | grep <new_ip>
   ```

**Current whitelist (NEVER REMOVE):**
- 62.76.130.37 (Owner IPv4)
- 43.98.167.164 (Agent IPv4)

**Note:** Removing these IPs will result in immediate lockout from VPS!

## 🚀 Landing Page Deployment

The landing page is located in `landing/app/dist/` (pre-built static files).

### Option A: Ansible Deployment (Recommended)

Deploy landing as part of infrastructure setup:

```bash
cd ansible
ansible-playbook site.yml --tags landing
```

This will:
- Create Dokku app `landing`
- Set nginx buildpack for static site
- Deploy files from `landing/app/dist/`
- Configure domain `clawtech.ru`
- Enable SSL with Let's Encrypt

### Option B: Manual Deployment Script

Use the provided deployment script:

```bash
./scripts/deploy-landing.sh
```

Requirements:
- SSH key configured at `/keys/clawtech-vps.pem`
- VPS accessible at `clawtech.ru:2233`

### Option C: Manual Git Push

Deploy directly using Dokku git workflow:

```bash
cd landing/app/dist

# Initialize git repo
git init
git add .
git commit -m "Landing deployment $(date)"

# Add Dokku remote
git remote add dokku dokku@clawtech.ru:landing

# Deploy
git push dokku main

# Configure domain (if not done automatically)
dokku domains:set landing clawtech.ru www.clawtech.ru

# Enable SSL
dokku letsencrypt:enable landing
```

### Post-Deployment Verification

After deployment, verify:

```bash
# Check app status
dokku apps:list
dokku ps:report landing

# Check domains
dokku domains:report landing

# Check SSL
dokku letsencrypt:list

# Test URL
curl -I https://clawtech.ru
```

### Landing Page Updates

To update landing page after changes:

1. **Rebuild if needed:**
   ```bash
   cd landing/app
   npm run build
   ```

2. **Redeploy using any option above**

3. **Verify deployment:**
   ```bash
   dokku ps:rebuild landing
   ```

## Emergency Procedures

### Lost SSH Access
1. Use SpaceWeb VNC console
2. Login as root
3. Check nftables: `nft list ruleset`
4. Verify whitelist IPs are present

### CrowdSec Blocking Legitimate Traffic
```bash
# Emergency whitelist for 24 hours
cscli decisions add -i <IP> --duration 24h

# Check what's happening
cscli alerts list
cscli decisions list
```

### Disk Full
```bash
# Check usage
df -h

# Clean logs
journalctl --vacuum-time=3d

# Rotate CrowdSec
cscli metrics flush
```

### Landing Page Down
```bash
# Check app status
dokku ps:report landing

# View logs
dokku logs landing -t

# Restart app
dokku ps:restart landing

# Check nginx logs
dokku nginx:logs landing
```
