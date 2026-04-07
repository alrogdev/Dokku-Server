# Dokku PaaS Server - Agent Guide

Infrastructure-as-code for a hardened Dokku PaaS server (VPS) managed via Ansible, with a React-based landing page.

## Project Overview

This project provides complete infrastructure automation for deploying a secure, production-ready Dokku PaaS server. It includes:

- **Infrastructure**: Ansible playbooks for VPS hardening and Dokku installation
- **Security**: nftables firewall, CrowdSec IDS, AIDE file integrity monitoring, Lynis auditing
- **Landing Page**: React + TypeScript + Vite static site deployed to Dokku
- **Domain**: clawtech.ru (VPS: 31.177.83.27)

## Technology Stack

### Infrastructure & Deployment
| Component | Technology |
|-----------|------------|
| IaC Tool | Ansible |
| PaaS Platform | Dokku (Docker-based) |
| Firewall | nftables |
| IDS/IPS | CrowdSec with Telegram alerts |
| FIM | AIDE (file integrity) |
| Auditing | Lynis |

### Landing Page (landing/app/)
| Component | Technology |
|-----------|------------|
| Framework | React 19 + TypeScript 5.9 |
| Build Tool | Vite 7.2.4 |
| Styling | Tailwind CSS 3.4.19 |
| UI Library | shadcn/ui (40+ components) |
| Animation | Framer Motion |
| Icons | Lucide React |
| Linting | ESLint 9 + typescript-eslint |

## Project Structure

```
.
├── ansible/                    # Infrastructure automation
│   ├── site.yml               # Main playbook (3 plays: base, security, dokku)
│   ├── inventory.ini          # Server connection details
│   ├── group_vars/all/
│   │   └── vars.yml           # Central configuration (IP, domain, whitelist)
│   └── roles/
│       ├── nftables/          # Firewall with IP whitelist
│       ├── crowdsec/          # IDS with Telegram notifications
│       ├── aide/              # File integrity monitoring
│       ├── lynis/             # Security auditing
│       ├── dokku-install/     # Dokku platform setup
│       ├── dokku-deploy/      # Deployment user configuration
│       └── landing/           # Landing page deployment
├── landing/
│   ├── app/                   # React application source
│   │   ├── src/
│   │   │   ├── sections/      # Page sections (Hero, Features, etc.)
│   │   │   ├── components/ui/ # shadcn/ui components (40+)
│   │   │   ├── hooks/         # React hooks (theme, mobile)
│   │   │   └── lib/           # Utilities
│   │   ├── dist/              # Pre-built static files for deployment
│   │   ├── package.json       # NPM dependencies
│   │   ├── vite.config.ts     # Vite configuration
│   │   └── tailwind.config.js # Tailwind theme customization
│   └── TechSpec.md            # Technical specification (Russian)
├── docs/
│   └── Dokku-project/         # Documentation
│       ├── AGENT.md           # Agent operational guidelines
│       ├── AI_AGENT_DEPLOY_GUIDE.md  # Deployment guide for apps
│       ├── MIGRATION.md       # VPS migration procedures
│       └── TOOLS.md           # Tool references
├── keys/
│   └── clawtech-vps.pem       # Symlink to SSH private key
├── scripts/
│   └── deploy-landing.sh      # Manual landing deployment script
└── opencode.jsonc             # OpenCode AI configuration
```

## Quick Start

### Deploy/Reconfigure Server

```bash
cd ansible
export TELEGRAM_BOT_TOKEN="your_token_here"
ansible-playbook -i inventory.ini site.yml
```

### Deploy Landing Page Only

```bash
# Option 1: Via Ansible
cd ansible
ansible-playbook -i inventory.ini site.yml --tags landing

# Option 2: Via script
./scripts/deploy-landing.sh

# Option 3: Manual git push
cd landing/app/dist
git init && git add . && git commit -m "Deploy"
git remote add dokku dokku@clawtech.ru:landing
git push dokku main --force
```

## Critical Configuration

### File: `ansible/group_vars/all/vars.yml`

Central configuration for the entire infrastructure:

```yaml
# Server Configuration
server_ip: "31.177.83.27"      # Change when migrating VPS
server_hostname: "clawtech"
domain: "clawtech.ru"

# SSH Configuration
ssh_port: 2233                  # Changes after initial setup
ssh_permit_root_login: prohibit-password

# ⚠️ CRITICAL: Whitelist IPs - NEVER REMOVE
whitelist_ips:
  - "62.76.130.37"             # Owner IPv4
  - "43.98.167.164"            # Agent IPv4
```

### Security Warning

**Removing whitelist IPs will result in immediate lockout from the VPS!** These IPs are whitelisted in both nftables and CrowdSec.

## Landing Page Development

### Build Commands

```bash
cd landing/app

# Development server
npm run dev

# Production build (outputs to dist/)
npm run build

# Lint code
npm run lint

# Preview production build
npm run preview
```

### Project Conventions

1. **Components**: Use shadcn/ui components from `src/components/ui/`
2. **Sections**: Page sections go in `src/sections/` (Hero, Features, etc.)
3. **Styling**: Use Tailwind classes with custom colors:
   - `bg-primary`: #0A0A0F (main background)
   - `bg-secondary`: #12121A
   - `accent-purple`: #8B5CF6
   - `accent-blue`: #3B82F6
   - `accent-cyan`: #06B6D4
4. **Theme**: Dark mode by default, toggleable via `useTheme` hook

### Key Files

| File | Purpose |
|------|---------|
| `src/App.tsx` | Main application component with background effects |
| `src/index.css` | Global styles, CSS variables, animations |
| `tailwind.config.js` | Theme customization, custom colors, animations |
| `vite.config.ts` | Build configuration, path aliases (@ → src) |
| `dist/static.json` | Dokku static site configuration |

## Server Access

```bash
# Initial setup (port 22)
ssh -p 22 -i keys/clawtech-vps.pem root@31.177.83.27

# After Ansible hardening (port 2233)
ssh -p 2233 -i keys/clawtech-vps.pem root@clawtech.ru
```

## Common Operations

### Check Security Status

```bash
# CrowdSec metrics
ssh root@clawtech.ru "cscli metrics"

# Firewall rules
ssh root@clawtech.ru "nft list ruleset"

# File integrity check
ssh root@clawtech.ru "aide --check"
```

### Dokku App Management

```bash
# List apps
ssh root@clawtech.ru "dokku apps:list"

# Check app status
ssh root@clawtech.ru "dokku ps:report landing"

# View logs
ssh root@clawtech.ru "dokku logs landing -t"

# Restart app
ssh root@clawtech.ru "dokku ps:restart landing"
```

### Deploy New Applications

See `docs/Dokku-project/AI_AGENT_DEPLOY_GUIDE.md` for detailed instructions.

Quick workflow:
```bash
# From your app directory
git remote add dokku dokku@clawtech.ru:appname
git push dokku main

# Set environment variables
ssh root@clawtech.ru "dokku config:set appname KEY=value"

# Enable SSL
ssh root@clawtech.ru "dokku letsencrypt:enable appname"
```

## Testing & Verification

### Before Deploying Changes

1. **Landing page build**:
   ```bash
   cd landing/app
   npm run build
   # Verify dist/ folder is updated
   ```

2. **Ansible syntax check**:
   ```bash
   cd ansible
   ansible-playbook -i inventory.ini site.yml --syntax-check
   ```

3. **Ansible dry run**:
   ```bash
   cd ansible
   ansible-playbook -i inventory.ini site.yml --check
   ```

## Security Considerations

### Implemented Protections

1. **Firewall (nftables)**: Whitelist-based access, blocks all except ports 22/2233, 80, 443
2. **CrowdSec**: Real-time threat detection with Telegram alerts
3. **AIDE**: Daily file integrity checks at 23:00 UTC
4. **Lynis**: Weekly security audits
5. **SSH Hardening**: Key-only auth, non-standard port (2233)

### Sensitive Data Handling

- **Telegram token**: Via environment variable only (`TELEGRAM_BOT_TOKEN`)
- **SSH keys**: Stored in `.opencode/openwork/inbox/`, symlinked to `keys/`
- **No secrets in git**: All sensitive data excluded via `.gitignore`

### Agent Limitations

**CANNOT do without explicit confirmation:**
- Change firewall rules
- Modify whitelist IPs
- Update system packages (apt upgrade)
- Add new SSH keys
- Remove or disable security tools (CrowdSec, AIDE, auditd)

## Troubleshooting

### SSH Connection Issues

```bash
# If port 2233 fails, try port 22 (initial setup)
ssh -p 22 -i keys/clawtech-vps.pem root@31.177.83.27

# Check nftables whitelist
ssh root@clawtech.ru "nft list set inet filter whitelist_ips"
```

### Landing Page Issues

```bash
# Check app status
ssh root@clawtech.ru "dokku ps:report landing"

# View logs
ssh root@clacktech.ru "dokku logs landing -n 100"

# Rebuild app
ssh root@clawtech.ru "dokku ps:rebuild landing"
```

### CrowdSec Blocking Traffic

```bash
# Emergency whitelist for 24 hours
ssh root@clawtech.ru "cscli decisions add -i <IP> --duration 24h"

# Check alerts
ssh root@clawtech.ru "cscli alerts list"
```

## Migration Notes

When moving to a new VPS:

1. Update `ansible/group_vars/all/vars.yml`:
   - `server_ip`
   - `domain` (if changing)
   
2. Update `ansible/inventory.ini` with new IP

3. Run Ansible playbook

4. Update DNS records to point to new IP

5. Verify SSL certificates are regenerated

## Documentation References

- **Agent Operations**: `docs/Dokku-project/AGENT.md`
- **App Deployment Guide**: `docs/Dokku-project/AI_AGENT_DEPLOY_GUIDE.md`
- **Migration Procedures**: `docs/Dokku-project/MIGRATION.md`
- **Landing Tech Spec**: `landing/TechSpec.md` (Russian)

## Notes for AI Agents

- SSH service name is `ssh` (not `sshd`) on Ubuntu 24.04
- Many Ansible tasks have `ignore_errors: yes` for idempotency
- The landing page `dist/` folder contains pre-built static files
- Dokku installs to `/usr/local/bin/dokku` with symlink to `/usr/bin/dokku`
- Playbook has 3 separate plays: base setup, security roles, dokku roles
