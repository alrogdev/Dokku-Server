# Dokku PaaS Security Architecture Design

**Date:** 2025-01-06  
**Project:** clawtech.ru VPS (SpaceWeb)  
**Version:** 1.0

---

## 1. Executive Summary

Secure PaaS platform based on Dokku for pet-projects with CIS Ubuntu 24.04 Level 1 compliance, CrowdSec protection, and automated security monitoring.

### Key Requirements
- CIS Ubuntu 24.04 Level 1 hardening
- CrowdSec with nftables firewall bouncer
- File Integrity Monitoring (AIDE)
- Weekly CIS audits (Lynis)
- Telegram security reports
- Support for Node.js, Python, PostgreSQL, SQLite, Redis

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
| Owner IPv6 | 2a0e:eac0:2020:37:8822:8c0f:c92e:ad16 | Admin access |
| Agent IPv4 | 43.98.167.164 | KimiClaw DevOps agent |

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
| SSH | Port 22, key-only auth, `PermitRootLogin=no` |
| Firewall | nftables (UFW disabled to avoid conflicts) |
| Auditd | Enabled with filesystem, auth, privilege rules |
| Kernel | `sysctl` hardening (rp_filter, syncookies, ICMP redirects) |
| File permissions | SUID/SGID audit, world-writable files |
| Accounts | Password policy, inactive lock, sudo logging |

### 4.2 Firewall Strategy

**No UFW** — direct nftables management to avoid conflicts with CrowdSec.

```nft
# Base nftables configuration
table inet filter {
    chain input {
        type filter hook input priority 0; policy drop;
        
        # Allow loopback
        iif "lo" accept
        
        # Allow established
        ct state established,related accept
        
        # Allow SSH, HTTP, HTTPS
        tcp dport {22, 80, 443} accept
        
        # Log and drop rest (for CrowdSec detection)
        log prefix "nftables dropped: " level warn
        drop
    }
}
```

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

### 4.4 File Integrity Monitoring (AIDE)

- **Monitored:** `/etc`, `/bin`, `/sbin`, `/usr`, `/var/log`, `/opt`
- **Excluded:** `/var/log/aide`, temp files, Dokku volumes
- **Schedule:** Daily at 02:00 MSK
- **Report:** Telegram notification with changes

### 4.5 CIS Auditing (Lynis)

- **Schedule:** Sundays at 03:00 MSK
- **Command:** `lynis audit system --quick`
- **Report:** Score + warnings + hardening status to Telegram

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
│       └── lynis-audit.sh         # Sundays 03:00 MSK
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
- Remove or modify whitelist IPs (62.76.130.37, 2a0e:eac0:2020:37:8822:8c0f:c92e:ad16, 43.98.167.164)

### 6.2 TOOLS.md Reference

```markdown
# Tools for VPS Access

## SSH Access
- **Key:** `/keys/clawtech-vps.pem`
- **Host:** `80.93.63.169` or `clawtech.ru`
- **User:** `root`
- **Command:** `ssh -i /keys/clawtech-vps.pem root@clawtech.ru`

## Documentation
- **Location:** `/docs/Dokku-project/`
- **Architecture:** `/docs/Dokku-project/ARCHITECTURE.md`
- **Incidents:** `/docs/Dokku-project/INCIDENT_RESPONSE.md`

## Useful Commands
- CrowdSec status: `cscli metrics`
- Nginx logs: `dokku nginx:logs <app>`
- App list: `dokku apps:list`
```

---

## 7. Reporting Schedule

| Report | Schedule | Content |
|--------|----------|---------|
| CrowdSec Summary | Every 6 hours | Attacks count, banned IPs, top countries, scenarios triggered, CAPI blocklist status |
| AIDE FIM | Daily 02:00 MSK | Files checked, changes detected, critical alerts |
| Lynis Audit | Sundays 03:00 MSK | CIS score, warnings, hardened items, recommendations |

---

## 8. Telegram Bot

- **Bot:** @Rogdev_Sec_alert_bot
- **Chat ID:** 1631006
- **Reports:** Summarized, not per-event (to avoid spam)

---

## 9. Dokku Plugins

| Plugin | Purpose |
|--------|---------|
| `dokku-postgres` | PostgreSQL databases |
| `dokku-redis` | Redis cache/sessions |
| `dokku-letsencrypt` | Auto SSL certificates |
| `dokku-sqlite3` | SQLite for simple projects |

---

## 10. Deployment Workflow

1. **Initial Setup:** Run Ansible playbook once
2. **Application Deploy:** `git push dokku main`
3. **Security Updates:** Ansible for system, cscli for CrowdSec
4. **Monitoring:** Automated cron scripts + Telegram
5. **Incident Response:** Documented in INCIDENT_RESPONSE.md

---

## 11. Security Checklist

- [ ] CIS Level 1 hardening applied
- [ ] SSH key-only authentication
- [ ] nftables configured (UFW disabled)
- [ ] CrowdSec installed with all collections
- [ ] CrowdSec bouncers (nginx + nftables) active
- [ ] CAPI blocklist subscribed
- [ ] Whitelist IPs configured
- [ ] AIDE initialized and scheduled
- [ ] Lynis installed and scheduled
- [ ] Telegram bot configured
- [ ] Cron scripts installed
- [ ] Dokku plugins installed
- [ ] SSL certificates configured
- [ ] Documentation created

---

## 12. Future Enhancements

- [ ] Off-site backups to S3
- [ ] Centralized logging (Loki/Grafana)
- [ ] Metrics dashboard
- [ ] Automated security patch management
- [ ] Multi-region deployment

---

**Approved by:** _________________  
**Date:** _________________
