# VPS Migration Guide

This document explains how to migrate the Dokku PaaS setup to a new VPS or deploy on multiple servers.

## Quick Migration Checklist

When moving to a new VPS, update these files:

### 1. Server IP Address
**File:** `ansible/group_vars/all/vars.yml`

```yaml
# Change this line
server_ip: "80.93.63.169"  # <-- New VPS IP
```

### 2. Domain Name (if changing)
**File:** `ansible/group_vars/all/vars.yml`

```yaml
# Change these lines
domain: "clawtech.ru"        # <-- New domain
server_hostname: "clawtech"  # <-- New hostname
```

### 3. SSH Port (if different)
**File:** `ansible/group_vars/all/vars.yml`

```yaml
# Change this line
ssh_port: 2233  # <-- New SSH port (or keep 22)
```

### 4. Inventory File
**File:** `ansible/inventory.ini`

```ini
# Change the hostname/IP
[new-server.com]  # <-- New server address
```

### 5. Whitelist IPs (add new admin IPs if needed)
**File:** `ansible/group_vars/all/vars.yml`

```yaml
whitelist_ips:
  - "62.76.130.37"      # Owner IPv4
  - "43.98.167.164"     # Agent IPv4
  - "NEW.IP.ADDRESS.HERE"  # <-- Add new admin IP
```

---

## Step-by-Step Migration

### Step 1: Prepare New VPS

1. **Create new VPS** with:
   - Ubuntu 24.04 LTS
   - Minimum 2 CPU, 4GB RAM, 45GB disk
   - Static IP address

2. **Generate new SSH keys for root** (or use existing):
   ```bash
   ssh-keygen -t ed25519 -f PETS-keys-new -C "root@new-server.com"
   ```

3. **Copy public key to new VPS** (via provider's console or initial setup)

### Step 2: Update Configuration

1. **Update all variables** in `ansible/group_vars/all/vars.yml`:
   ```yaml
   server_ip: "NEW.IP.ADDRESS.HERE"
   domain: "new-domain.com"
   server_hostname: "newhostname"
   ```

2. **Update inventory** in `ansible/inventory.ini`:
   ```ini
   [prod]
   new-domain.com ansible_port=2233 ansible_user=root ansible_ssh_private_key_file=../keys/PETS-keys-new
   ```

3. **Place new SSH key**:
   ```bash
   cp PETS-keys-new .opencode/private/
   cd keys && ln -sf ../.opencode/private/PETS-keys-new clawtech-vps.pem
   ```

### Step 3: Run Ansible Playbook

```bash
cd ansible

# Test connectivity
ansible -m ping prod

# Run in check mode first
ansible-playbook site.yml --check --diff

# Deploy to new server
ansible-playbook site.yml
```

### Step 4: Verify Deployment

```bash
# SSH to new server
ssh -p 2233 -i keys/clawtech-vps.pem root@new-domain.com

# Check services
systemctl status crowdsec
dokku version
cscli metrics

# Test landing page
curl -I https://new-domain.com
```

### Step 5: Setup Monitoring

```bash
cd scripts
export TELEGRAM_BOT_TOKEN="your_token"
./setup-cron.sh
```

### Step 6: Update DNS

1. Point domain A-record to new IP
2. Wait for DNS propagation
3. Verify SSL certificate: `dokku letsencrypt:enable landing`

---

## Multi-Server Deployment

To deploy on multiple servers simultaneously:

### 1. Update Inventory

**File:** `ansible/inventory.ini`

```ini
[prod]
server1.clawtech.ru ansible_host=80.93.63.169
server2.clawtech.ru ansible_host=80.93.63.170
server3.clawtech.ru ansible_host=80.93.63.171

[prod:vars]
ansible_port=2233
ansible_user=root
ansible_ssh_private_key_file=../keys/clawtech-vps.pem
ansible_python_interpreter=/usr/bin/python3
```

### 2. Create Host-Specific Variables (if needed)

**File:** `ansible/host_vars/server1.clawtech.ru.yml`

```yaml
server_ip: "80.93.63.169"
domain: "server1.clawtech.ru"
```

### 3. Deploy to All Servers

```bash
ansible-playbook site.yml
```

Or deploy to specific server:

```bash
ansible-playbook site.yml --limit server1.clawtech.ru
```

---

## Rollback Plan

If migration fails:

1. **Keep old VPS running** until new one verified
2. **Don't update DNS** until fully tested
3. **Quick rollback**: Update DNS back to old IP

---

## Files to Never Change During Migration

These files should remain constant:

- `keys/dokku-deploy/id_ed25519` - Deployment keys
- `scripts/*` - Monitoring scripts (auto-detect IP)
- `docs/*` - Documentation (IP mentioned for reference only)

---

## Migration Checklist

- [ ] New VPS created with Ubuntu 24.04
- [ ] SSH keys generated and placed in `.opencode/private/`
- [ ] `ansible/group_vars/all/vars.yml` updated with new IP
- [ ] `ansible/inventory.ini` updated with new hostname
- [ ] Whitelist IPs verified (add new admin IPs if needed)
- [ ] Ansible playbook tested in check mode
- [ ] Deployment completed successfully
- [ ] Services verified (CrowdSec, Dokku, AIDE, Lynis)
- [ ] Cron jobs installed and tested
- [ ] Landing page deployed and accessible
- [ ] DNS updated (after verification)
- [ ] SSL certificates working
- [ ] Telegram notifications working
- [ ] Old VPS can be terminated (after 48h monitoring)

---

## Troubleshooting Migration

### SSH Connection Fails
```bash
# Check key permissions
chmod 600 keys/clawtech-vps.pem

# Test with verbose output
ssh -v -p 2233 -i keys/clawtech-vps.pem root@new-server.com
```

### Ansible Fails
```bash
# Check inventory
ansible-inventory --list

# Test specific host
ansible -m ping new-server.com

# Run with verbose output
ansible-playbook site.yml -vvv
```

### Services Not Starting
```bash
# Check logs on new server
journalctl -xe

# Verify configuration
cat /etc/nftables.conf
cscli config show
```

---

## Summary

**Single source of truth for server configuration:**
- IP: `ansible/group_vars/all/vars.yml` → `server_ip`
- Domain: `ansible/group_vars/all/vars.yml` → `domain`
- SSH Port: `ansible/group_vars/all/vars.yml` → `ssh_port`

**To migrate:** Update 3-4 lines in `vars.yml` and run Ansible playbook.
