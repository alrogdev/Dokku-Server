# Tools for VPS Access

## Server Configuration

**Central Configuration File:** `ansible/group_vars/all/vars.yml`

To change server IP, domain, or SSH port - edit this file only!

```yaml
server_ip: "80.93.63.169"      # <-- Change for new VPS
domain: "clawtech.ru"          # <-- Change for new domain
ssh_port: 2233                 # <-- Change SSH port
```

See [MIGRATION.md](MIGRATION.md) for detailed migration instructions.

---

## SSH Access

### Root Access (Full Control)

**Key:** `keys/clawtech-vps.pem` (symlink to `.opencode/private/PETS-keys`)

```bash
ssh -p 2233 -i keys/clawtech-vps.pem root@clawtech.ru
```

### Dokku-Deploy Access (Deployment Only)

**Key:** `keys/dokku-deploy/id_ed25519`

```bash
# For manual access
ssh -p 2233 -i keys/dokku-deploy/id_ed25519 dokku-deploy@clawtech.ru

# For git deployment
ssh-add keys/dokku-deploy/id_ed25519
git push dokku main
```

---

## Ansible Commands

### Deploy Everything

```bash
cd ansible
ansible-playbook site.yml
```

### Check Specific Host

```bash
ansible -m ping prod
```

### Deploy Specific Role

```bash
ansible-playbook site.yml --tags crowdsec
```

---

## Useful Server Commands

### CrowdSec

```bash
# Check status
cscli metrics

# List banned IPs
cscli decisions list

# View alerts
cscli alerts list

# Update collections
cscli collections upgrade -a
```

### Dokku

```bash
# List apps
dokku apps:list

# App logs
dokku logs <app> -t

# App status
dokku ps:report <app>

# Restart app
dokku ps:restart <app>

# Environment variables
dokku config:show <app>
```

### System

```bash
# Resource usage
htop
free -h
df -h

# Service status
systemctl status crowdsec
systemctl status nftables
systemctl status dokku

# Network
nft list ruleset
ss -tlnp
```

---

## Monitoring Scripts

### Manual Run

```bash
cd scripts

# CrowdSec report
./cron/crowdsec-report.sh

# AIDE check
./cron/aide-check.sh

# Lynis audit
./cron/lynis-audit.sh

# Resource monitor
./cron/resource-monitor.sh
```

### View Logs

```bash
# CrowdSec logs
tail -f /var/log/crowdsec-report.log

# AIDE logs
tail -f /var/log/aide-check.log

# All cron logs
tail -f /var/log/syslog | grep CRON
```

---

## Documentation

- **Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Agent Guide:** [AGENT.md](AGENT.md)
- **Operator Handbook:** [OPERATOR.md](OPERATOR.md)
- **Migration Guide:** [MIGRATION.md](MIGRATION.md)
- **AI Deploy Guide:** [AI_AGENT_DEPLOY_GUIDE.md](AI_AGENT_DEPLOY_GUIDE.md)

---

## Emergency Contacts

- **Telegram Bot:** @Rogdev_Sec_alert_bot
- **Server Provider:** SpaceWeb (VNC console available)
- **Domain:** TimeWebCloud
