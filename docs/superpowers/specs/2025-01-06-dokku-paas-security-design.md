# Dokku PaaS Security Architecture Design

**Date:** 2025-01-06  
**Project:** clawtech.ru VPS (SpaceWeb)  
**Version:** 1.1 (Updated after LLM review)

---

## 1. Executive Summary

Secure PaaS platform based on Dokku for pet-projects with CIS Ubuntu 24.04 Level 1 compliance (with practical deviations), CrowdSec protection, and automated security monitoring.

### Key Requirements
- CIS Ubuntu 24.04 Level 1 hardening (with `PermitRootLogin=prohibit-password`)
- SSH port 2233 (non-standard)
- IPv6 completely disabled
- CrowdSec with nftables firewall bouncer
- File Integrity Monitoring (AIDE)
- Weekly CIS audits (Lynis)
- Telegram security reports
- Resource monitoring (CPU/RAM alerts)
- Fail2ban fallback for SSH
- Support for Node.js, Python, PostgreSQL, SQLite (persistent), Redis

---

## 2. Infrastructure

### 2.1 VPS Specifications
- **Provider:** SpaceWeb
- **IP:** 80.93.63.169
- **Domain:** clawtech.ru (*.clawtech.ru A-record)
- **Specs:** 2 CPU, 4 GB RAM, 45 GB NVMe
- **OS:** Ubuntu 24.04 LTS

### 2.2 Whitelist IPs
| Type | IP | Purpose |
|------|-----|---------|
| Owner IPv4 | 62.76.130.37 | Admin access |
| Agent IPv4 | 43.98.167.164 | KimiClaw DevOps agent |

**Note:** IPv6 completely disabled at kernel level.

---

## 3. Architecture

### 3.1 High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                    SpaceWeb VPS (Ubuntu 24.04)              │
│                    80.93.63.169 / clawtech.ru               │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  CIS Level 1 │  │    Dokku     │  │   CrowdSec       │  │
│  │  Hardening   │  │  (Docker)    │  │  + Collections   │  │
│  │              │  │              │  │  + CAPI Blocklist│  │
│  │  • SSH keys  │  │  • Node.js   │  │  + Telegram      │  │
│  │  • nftables  │  │  • Python    │  │    notifications │  │
│  │  • Auditd    │  │  • PG/Redis  │  │                  │  │
│  │  • AIDE      │  │  • SQLite    │  │  • nginx         │  │
│  │  • Lynis     │  │              │  │  • docker        │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │              Monitoring & Reporting                    │ │
│  │  • FIM (AIDE) nightly at 02:00 MSK → Telegram        │ │
│  │  • CrowdSec summary every 6h → Telegram              │ │
│  │  • CIS audit (Lynis) Sundays → Telegram              │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌──────────────────────────────┐
              │   Telegram: @Rogdev_Sec_alert_bot  │
              └──────────────────────────────┘
```

### 3.2 Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| PaaS Platform | Dokku | Application deployment |
| Container Runtime | Docker | Application isolation |
| Reverse Proxy | Nginx | HTTP routing, SSL |
| Firewall | nftables + CrowdSec | Network security |
| IDS/IPS | CrowdSec | Threat detection |
| FIM | AIDE | File integrity monitoring |
| Audit | Lynis | CIS compliance checking |
| Automation | Ansible | Infrastructure as code |
| Reporting | Shell scripts + Telegram API | Security notifications |

---

## 4. Security Components

### 4.1 CIS Ubuntu 24.04 Level 1 Hardening

Ansible role `cis-hardening/` configures:

| Control | Implementation |
|---------|---------------|
| SSH | Port **2233**, key-only auth, `PermitRootLogin=prohibit-password` |
| Firewall | nftables (UFW disabled to avoid conflicts) |
| IPv6 | Completely disabled (sysctl + grub) |
| Auditd | Enabled with filesystem, auth, privilege rules |
| Kernel | `sysctl` hardening (rp_filter, syncookies, ICMP redirects) |
| File permissions | SUID/SGID audit, world-writable files |
| Accounts | Password policy, inactive lock, sudo logging |
| Swap | 2GB swap file configured |
| Logrotate | Configured for CrowdSec, nginx, auditd |
| Auto-updates | `unattended-upgrades` for security patches |

### 4.2 Firewall Strategy

**No UFW** — direct nftables management to avoid conflicts with CrowdSec.

```nft
# Base nftables configuration
table inet filter {
    chain input {
        type filter hook input priority 0; policy drop;
        
        # Whitelist trusted IPs (CRITICAL - never remove)
        ip saddr { 62.76.130.37, 43.98.167.164 } accept
        
        # Allow loopback
        iif "lo" accept
        
        # Allow established
        ct state established,related accept
        
        # Allow SSH (port 2233), HTTP, HTTPS
        tcp dport {2233, 80, 443} accept
        
        # Rate limit SSH to prevent brute force noise
        tcp dport 2233 ct state new limit rate 3/minute accept
        
        # Log and drop rest (for CrowdSec detection)
        log prefix "nftables dropped: " level warn
        drop
    }
    
    chain forward {
        type filter hook forward priority 0; policy accept;
        # Docker/Dokku connectivity
        iifname "docker0" accept
        iifname "br-*" accept
        ct state established,related accept
        drop
    }
}
```

**Important:** Whitelist IPs are configured in BOTH nftables and CrowdSec to prevent lockout.

### 4.3 CrowdSec Configuration

#### Collections Installed
| Collection | Purpose |
|------------|---------|
| `crowdsecurity/nginx` | Nginx log parsing |
| `crowdsecurity/docker` | Docker log parsing |
| `crowdsecurity/sshd` | SSH brute-force detection |
| `crowdsecurity/linux` | Core Linux support |
| `crowdsecurity/postgresql` | PostgreSQL protection |
| `crowdsecurity/base-http-scenarios` | HTTP attacks (SQLi, XSS, LFI) |
| `crowdsecurity/appsec-virtual-patching` | CVE protection |
| `crowdsecurity/appsec-generic-rules` | Generic WAF rules |
| `crowdsecurity/auditd` | Auditd monitoring |
| `crowdsecurity/auditd-postexploit-exec-from-net` | Post-exploitation detection |
| `crowdsecurity/ssh-slow-bf` | Slow SSH brute-force |
| `crowdsecurity/ssh-bf_user-enum` | User enumeration |
| `crowdsecurity/iptables-scan-multi_ports` | Port scan detection (works with nftables) |

#### Bouncers
- `crowdsec-nginx-bouncer` — HTTP-level blocking
- `crowdsec-firewall-bouncer-nftables` — IP-level blocking

#### Community Blocklist (CAPI)
- **Free subscription** — 10K-50K IPs from community
- **Auto-updates** every 15 minutes
- **Origin:** CAPI decisions automatically applied

#### SSH Ban Strategy
| Scenario | Detection | Duration |
|----------|-----------|----------|
| `ssh-bf` | 5 attempts / 10 sec | 4 hours |
| `ssh-slow-bf` | 3 attempts / 1 hour | 24 hours |
| `ssh-bf_user-enum` | 3 users / 10 sec | 4 hours |
| Repeat offenders | Exponential backoff | Up to 7 days |

#### Whitelist Configuration
**Critical:** Whitelist IPs in BOTH nftables AND CrowdSec to prevent admin lockout.

```yaml
# /etc/crowdsec/parsers/s02-enrich/whitelist.yaml
name: crowdsecurity/whitelist-good-actors
whitelist:
  reason: "Trusted admin and agent IPs"
  ip:
    - "62.76.130.37"
    - "43.98.167.164"
```

**Note:** These IPs are also whitelisted in nftables (see Firewall Strategy).

### 4.4 File Integrity Monitoring (AIDE)

- **Monitored:** `/etc`, `/bin`, `/sbin`, `/usr/bin`, `/usr/sbin`, `/var/log` (reduced scope for 4GB RAM)
- **Excluded:** `/var/log/aide`, `/usr/share`, temp files, Dokku volumes, Docker data
- **Schedule:** Daily at 02:00 MSK
- **Execution:** `nice -n 10 ionice -c 3` (low CPU/IO priority)
- **Timeout:** 60 minutes (script fails if exceeded)
- **Report:** Telegram notification with changes

### 4.5 CIS Auditing (Lynis)

- **Schedule:** Sundays at 03:00 MSK (1 hour after AIDE to avoid overlap)
- **Command:** `lynis audit system --quick`
- **Timeout:** 30 minutes
- **Report:** Score + warnings + hardening status to Telegram

### 4.6 Fail2ban Fallback

Minimal fail2ban configuration as safety net if CrowdSec fails:

```ini
# /etc/fail2ban/jail.local
[sshd]
enabled = true
port = 2233
filter = sshd
logpath = /var/log/auth.log
maxretry = 10
findtime = 1h
bantime = 1h
```

**Note:** Fail2ban uses relaxed parameters to avoid conflicts with CrowdSec.

### 4.7 Resource Monitoring

Automated monitoring with Telegram alerts:

| Metric | Threshold | Window | Action |
|--------|-----------|--------|--------|
| CPU | >90% | 20 min average | Telegram alert with top processes |
| RAM | >90% | 20 min average | Telegram alert with memory usage |
| Disk | >90% | Immediate | Critical alert |
| Load Average | >4 (2 CPU * 2) | 15 min | Warning alert |

**Rate limiting:** Max 1 alert per hour per metric to avoid spam.

---

## 5. Project Structure

```
paas-dokku/
├── ansible/
│   ├── inventory.ini              # Hosts (prod: 80.93.63.169)
│   ├── ansible.cfg                # Configuration
│   ├── site.yml                   # Main playbook
│   ├── group_vars/
│   │   └── all/
│   │       └── vars.yml           # Public variables
│   └── roles/
│       ├── cis-hardening/         # CIS Ubuntu 24.04 Level 1
│       ├── dokku/                 # Dokku + plugins
│       ├── crowdsec/              # CrowdSec + collections
│       ├── aide/                  # FIM
│       └── lynis/                 # CIS audit
├── scripts/
│   ├── lib/
│   │   └── telegram.sh            # Telegram notification library
│   └── cron/
│       ├── crowdsec-report.sh     # Every 6 hours
│       ├── aide-check.sh          # Daily 02:00 MSK
│       ├── lynis-audit.sh         # Sundays 03:00 MSK
│       └── update-geoip.sh        # Weekly GeoIP update
├── docs/
│   └── Dokku-project/
│       ├── AGENT.md               # Agent guidelines
│       ├── OPERATOR.md            # Operator handbook
│       ├── ARCHITECTURE.md        # System architecture
│       ├── INCIDENT_RESPONSE.md   # Incident procedures
│       └── CHANGELOG.md           # Change history
├── keys/
│   ├── clawtech-vps.pem           # SSH key (encrypted)
│   ├── clawtech-vps.pub           # Public key
│   └── README.md                  # Key usage instructions
└── TOOLS.md                       # Tools reference
```

---

## 6. Agent Documentation

### 6.1 AGENT.md — Guidelines for KimiClaw Agent

**✅ CAN DO:**
- Read all documents in `/docs/Dokku-project/`
- Execute commands on VPS via SSH using key from `/keys/`
- Monitor logs, service status, metrics
- Create and send reports to Telegram
- Propose configuration changes (apply only after confirmation)
- Deploy applications via Dokku (git push)
- Restart services on failure
- Update CrowdSec collections

**❌ CANNOT DO:**
- Change root password or SSH keys
- Disable auditd, AIDE, or CrowdSec
- Modify CIS hardening policies
- Delete backups
- Expose private data (tokens, keys) in unsecured channels

**⚠️ REQUIRES CONFIRMATION:**
- Change firewall rules
- Update system packages (apt upgrade)
- Modify Dokku configuration
- Add new SSH keys
- Remove or modify whitelist IPs (62.76.130.37, 43.98.167.164)

**🔴 CRITICAL: Whitelist IP Management**

When adding new IPs to whitelist:
1. **nftables:** Add to `set whitelist_ips` in `/etc/nftables.conf`
2. **CrowdSec:** Add to `/etc/crowdsec/parsers/s02-enrich/whitelist.yaml`
3. **Reload:** `nft -f /etc/nftables.conf && systemctl reload crowdsec`
4. **Verify:** `cscli decisions list -a | grep <ip>` (should show whitelisted)

**Current whitelist (NEVER REMOVE):**
- 62.76.130.37 (Owner IPv4)
- 43.98.167.164 (Agent IPv4)

**Note:** Removing these IPs will result in immediate lockout from VPS!

### 6.2 TOOLS.md Reference

```markdown
# Tools for VPS Access

## SSH Access
- **Key:** `/keys/clawtech-vps.pem`
- **Host:** `80.93.63.169` or `clawtech.ru`
- **Port:** `2233` (non-standard)
- **User:** `root`
- **Command:** `ssh -p 2233 -i /keys/clawtech-vps.pem root@clawtech.ru`

## Documentation
- **Location:** `/docs/Dokku-project/`
- **Architecture:** `/docs/Dokku-project/ARCHITECTURE.md`
- **Incidents:** `/docs/Dokku-project/INCIDENT_RESPONSE.md`

## Useful Commands
- CrowdSec status: `cscli metrics`
- Nginx logs: `dokku nginx:logs <app>`
- App list: `dokku apps:list`
- System resources: `htop` or `free -h`
```

---

## 7. Reporting Schedule

| Report | Schedule | Content |
|--------|----------|---------|
| CrowdSec Summary | Every 6 hours | Attacks count, banned IPs, top countries, scenarios triggered, CAPI blocklist status, cscli metrics |
| AIDE FIM | Daily 02:00 MSK | Files checked, changes detected, critical alerts (timeout: 60 min) |
| Lynis Audit | Sundays 03:00 MSK | CIS score, warnings, hardened items, recommendations (timeout: 30 min) |
| Resource Monitor | Continuous | CPU/RAM >90% for 20 min → Telegram alert (max 1/hour) |
| Disk Monitor | Every 15 min | Disk >90% → Immediate critical alert |
| GeoIP Update | Sundays 04:00 MSK | Update CrowdSec GeoIP database, hub update, collections upgrade |

---

## 8. Telegram Bot

- **Bot:** @Rogdev_Sec_alert_bot
- **Chat ID:** 1631006
- **Reports:** Summarized, not per-event (to avoid spam)

---

## 9. Dokku Plugins

| Plugin | Purpose | Notes |
|--------|---------|-------|
| `dokku-postgres` | PostgreSQL databases | Persistent data |
| `dokku-redis` | Redis cache/sessions | Persistent data |
| `dokku-letsencrypt` | Auto SSL certificates | Wildcard for *.clawtech.ru |
| `dokku-sqlite3` | SQLite for simple projects | **Requires persistent volume** |

---

## 10. Deployment Workflow

1. **Initial Setup:** Run Ansible playbook once
2. **Application Deploy:** `git push dokku main`
3. **Security Updates:** Ansible for system, cscli for CrowdSec
4. **Monitoring:** Automated cron scripts + Telegram
5. **Incident Response:** Documented in INCIDENT_RESPONSE.md

---

## 11. Security Checklist

- [ ] CIS Level 1 hardening applied (with `PermitRootLogin=prohibit-password`)
- [ ] SSH port changed to 2233
- [ ] IPv6 completely disabled
- [ ] SSH key-only authentication
- [ ] nftables configured with whitelist and Docker forward rules (UFW disabled)
- [ ] CrowdSec installed with all collections
- [ ] CrowdSec whitelist configured for admin IPs
- [ ] CrowdSec bouncers (nginx + nftables) active
- [ ] CAPI blocklist subscribed
- [ ] Fail2ban fallback configured for SSH
- [ ] AIDE initialized with reduced scope and scheduled (timeout: 60 min)
- [ ] Lynis installed and scheduled (timeout: 30 min)
- [ ] Logrotate configured for all services
- [ ] Swap 2GB configured
- [ ] Resource monitoring scripts installed
- [ ] Telegram bot configured
- [ ] Cron scripts installed with timeouts
- [ ] Dokku plugins installed
- [ ] SQLite persistent storage configured
- [ ] SSL certificates configured
- [ ] **GeoIP database auto-update configured (weekly)**
- [ ] Documentation created

---

## 12. Future Enhancements

- [ ] Off-site backups to S3
- [ ] Centralized logging (Loki/Grafana)
- [ ] Metrics dashboard
- [ ] Multi-region deployment
- [ ] Docker container health monitoring
- [ ] Automated SSL renewal alerts

---

## Appendix A: SQLite Persistent Storage

For SQLite databases in Dokku, use persistent storage:

```bash
# Create storage directory on host
dokku storage:ensure-directory myapp

# Mount to container
dokku storage:mount myapp /var/lib/dokku/data/storage/myapp:/app/data

# In application, use /app/data/database.db
```

**Note:** Without persistent storage, SQLite data is lost on `dokku ps:rebuild`.

---

## Appendix B: CrowdSec AppSec Performance

`appsec-virtual-patching` is enabled but monitored for performance impact:

- **If CPU usage > 80% sustained:** Consider disabling AppSec
- **If latency > 500ms:** Review WAF rules
- **Alternative:** Use only `base-http-scenarios` for lighter load

---

## Appendix C: Disaster Recovery

### Quick Recovery Steps

1. **Lost SSH access:**
   - Use SpaceWeb VNC console
   - Login as root
   - Check nftables: `nft list ruleset`
   - Verify whitelist IPs

2. **CrowdSec blocking legitimate traffic:**
   - Emergency whitelist: `cscli decisions add -i <IP> --duration 24h`
   - Check alerts: `cscli alerts list`
   - Review decisions: `cscli decisions list`

3. **Disk full:**
   - Check usage: `df -h`
   - Clean logs: `journalctl --vacuum-time=3d`
   - Rotate CrowdSec: `cscli metrics flush`

4. **Complete rebuild:**
   - Run Ansible playbook from fresh Ubuntu 24.04
   - Restore Dokku apps from git repos
   - Restore databases from backups (if configured)

---

**Approved by:** _________________  
**Date:** _________________
