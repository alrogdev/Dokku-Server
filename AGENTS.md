# Dokku PaaS Server - Agent Guide

Infrastructure-as-code for a hardened Dokku PaaS server (VPS) managed via Ansible.

## Quick Start

```bash
# Deploy/reconfigure server
cd ansible
export TELEGRAM_BOT_TOKEN="..."
ansible-playbook -i inventory.ini site.yml
```

## Critical Paths

| Purpose | Location |
|---------|----------|
| Main playbook | `ansible/site.yml` |
| Inventory | `ansible/inventory.ini` |
| Server config (IP, domain, whitelist) | `ansible/group_vars/all/vars.yml` |
| SSH keys (private) | `.opencode/openwork/inbox/PETS-keys` |
| SSH keys (symlink) | `keys/clawtech-vps.pem` → `../.opencode/openwork/inbox/PETS-keys` |
| Agent docs | `docs/Dokku-project/AGENT.md` |

## Server Access

```bash
# Current VPS: 31.177.83.27 (clawtech.ru)
# SSH port: 22 (initial), 2233 (after Ansible)

# Connect via symlink (port 22 for initial setup)
ssh -p 22 -i keys/clawtech-vps.pem root@31.177.83.27

# Or directly
ssh -p 22 -i .opencode/openwork/inbox/PETS-keys root@31.177.83.27
```

## Central Configuration

**File:** `ansible/group_vars/all/vars.yml`

Key variables for migration:
- `server_ip` - VPS IP address
- `domain` - Primary domain (clawtech.ru)
- `ssh_port` - SSH port (2233 after hardening)
- `whitelist_ips` - **NEVER REMOVE** (lockout protection)

## Running Ansible

```bash
cd ansible

# Set Telegram token for CrowdSec notifications
export TELEGRAM_BOT_TOKEN="8756634941:AAHbb2NAG77TuRLPoD2A6asU3ExXVQ-yMwc"

# Full deployment
ansible-playbook -i inventory.ini site.yml

# Check only
ansible-playbook -i inventory.ini site.yml --check
```

## ⚠️ CRITICAL: Whitelist IPs

**Current whitelist (removing = lockout):**
- `62.76.130.37` - Owner IPv4
- `43.98.167.164` - Agent IPv4

To add new IPs:
1. Edit `ansible/group_vars/all/vars.yml` → `whitelist_ips`
2. Re-run Ansible

## Common Tasks

```bash
# Check CrowdSec status
ssh root@clawtech.ru "cscli metrics"

# Check nftables rules
ssh root@clawtech.ru "nft list ruleset"

# View Dokku apps (after deployment)
ssh root@clawtech.ru "dokku apps:list"
```

## Project Structure

```
ansible/
  site.yml              # Main playbook (3 plays: base, security, dokku)
  inventory.ini         # Server connection details
  group_vars/all/       # Central config (IP, domain, whitelist)
  roles/
    nftables/           # Firewall with whitelist
    crowdsec/           # IDS with Telegram alerts
    aide/               # File integrity monitoring
    lynis/              # Security auditing
    dokku-deploy/       # Deployment user setup
    landing/            # Static site deployment
keys/
  clawtech-vps.pem      # Symlink to root SSH key
  dokku-deploy/         # Auto-generated deploy key
docs/
  Dokku-project/        # Full documentation
landing/app/dist/       # Pre-built static landing page
```

## Notes

- **SSH service name:** `ssh` (not `sshd`) on Ubuntu 24.04
- **Dokku install:** Via apt from packagecloud repo (not from install.sh directly)
- **Playbook structure:** 3 separate plays - base setup, security roles, dokku roles
- **Ignore_errors:** Many tasks have `ignore_errors: yes` for idempotency
- **Sensitive data:** Telegram token via env var, SSH keys in `.opencode/private/`

## Troubleshooting

```bash
# SSH connection refused on 2233? 
# Check if Ansible completed SSH configuration
ssh -p 22 -i .opencode/openwork/inbox/PETS-keys root@31.177.83.27

# Dokku not found after install?
# It installs to /usr/local/bin/dokku, symlink created in playbook

# CrowdSec errors?
# Check profiles.yaml format - field names changed in v1.6
```
