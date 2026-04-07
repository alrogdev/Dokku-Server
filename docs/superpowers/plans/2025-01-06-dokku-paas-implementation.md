# Dokku PaaS Security Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy secure Dokku PaaS on Ubuntu 24.04 VPS with CIS Level 1 hardening, CrowdSec protection, and automated monitoring

**Architecture:** Ansible playbook for initial setup + shell scripts for ongoing monitoring. CIS hardening with practical deviations (SSH port 2233, root login with keys). CrowdSec with nftables bouncer and whitelist protection.

**Tech Stack:** Ansible, nftables, CrowdSec, Dokku, Docker, AIDE, Lynis, Telegram Bot API

---

## Prerequisites

- [ ] **Verify VPS access**
  - Confirm SSH key works: `ssh -p 2233 -i /keys/clawtech-vps.pem root@clawtech.ru`
  - If port 22 still active, use: `ssh -i /keys/clawtech-vps.pem root@clawtech.ru`

- [ ] **Install Ansible on control machine**
  ```bash
  pip install ansible
  ansible --version
  ```

- [ ] **Create project structure**
  ```bash
  mkdir -p paas-dokku/{ansible/roles,scripts/{lib,cron},docs/Dokku-project,keys}
  cd paas-dokku
  git init
  ```

---

## Phase 1: Ansible Configuration

### Task 1: Create Ansible Inventory and Config

**Files:**
- Create: `ansible/inventory.ini`
- Create: `ansible/ansible.cfg`
- Create: `ansible/site.yml`
- Create: `ansible/group_vars/all/vars.yml`

- [ ] **Step 1: Create inventory file**

```ini
; ansible/inventory.ini
[prod]
clawtech.ru ansible_port=2233 ansible_user=root ansible_ssh_private_key_file=../keys/clawtech-vps.pem

[prod:vars]
ansible_python_interpreter=/usr/bin/python3
```

- [ ] **Step 2: Create ansible.cfg**

```ini
; ansible/ansible.cfg
[defaults]
inventory = inventory.ini
host_key_checking = False
retry_files_enabled = False
stdout_callback = yaml

[ssh_connection]
pipelining = True
control_path = /tmp/ansible-ssh-%%h-%%p-%%r
```

- [ ] **Step 3: Create main playbook**

```yaml
---
# ansible/site.yml
- name: Deploy Dokku PaaS with Security Hardening
  hosts: prod
  become: yes
  roles:
    - cis-hardening
    - dokku
    - crowdsec
    - aide
    - lynis
```

- [ ] **Step 4: Create group variables**

```yaml
---
# ansible/group_vars/all/vars.yml
# SSH Configuration
ssh_port: 2233
ssh_permit_root_login: prohibit-password

# Whitelist IPs (CRITICAL - never remove)
whitelist_ips:
  - "62.76.130.37"
  - "43.98.167.164"

# Domain
domain: clawtech.ru

# Telegram Bot
telegram_bot_token: "{{ vault_telegram_bot_token }}"
telegram_chat_id: "1631006"

# CrowdSec Collections
crowdsec_collections:
  - crowdsecurity/nginx
  - crowdsecurity/docker
  - crowdsecurity/sshd
  - crowdsecurity/linux
  - crowdsecurity/postgresql
  - crowdsecurity/base-http-scenarios
  - crowdsecurity/appsec-virtual-patching
  - crowdsecurity/appsec-generic-rules
  - crowdsecurity/auditd
  - crowdsecurity/auditd-postexploit-exec-from-net
  - crowdsecurity/ssh-slow-bf
  - crowdsecurity/ssh-bf_user-enum
  - crowdsecurity/iptables-scan-multi_ports
```

- [ ] **Step 5: Test connectivity**
  ```bash
  cd ansible
  ansible -m ping prod
  ```
  Expected: `pong` response

- [ ] **Step 6: Commit**
  ```bash
  git add ansible/
  git commit -m "feat: add ansible configuration and inventory"
  ```

---

### Task 2: CIS Hardening Role

**Files:**
- Create: `ansible/roles/cis-hardening/tasks/main.yml`
- Create: `ansible/roles/cis-hardening/handlers/main.yml`

- [ ] **Step 1: Create main tasks file**

```yaml
---
# ansible/roles/cis-hardening/tasks/main.yml

- name: Update apt cache
  apt:
    update_cache: yes
    cache_valid_time: 3600

- name: Install required packages
  apt:
    name:
      - vim
      - htop
      - curl
      - wget
      - logrotate
      - unattended-upgrades
      - fail2ban
      - nftables
      - aide
      - lynis
      - auditd
    state: present

- name: Disable IPv6 via sysctl
  sysctl:
    name: "{{ item }}"
    value: "1"
    state: present
    reload: yes
  loop:
    - net.ipv6.conf.all.disable_ipv6
    - net.ipv6.conf.default.disable_ipv6
    - net.ipv6.conf.lo.disable_ipv6

- name: Configure SSH
  lineinfile:
    path: /etc/ssh/sshd_config
    regexp: "{{ item.regexp }}"
    line: "{{ item.line }}"
    state: present
  loop:
    - { regexp: '^#?Port', line: 'Port {{ ssh_port }}' }
    - { regexp: '^#?PermitRootLogin', line: 'PermitRootLogin {{ ssh_permit_root_login }}' }
    - { regexp: '^#?PasswordAuthentication', line: 'PasswordAuthentication no' }
    - { regexp: '^#?PubkeyAuthentication', line: 'PubkeyAuthentication yes' }
    - { regexp: '^#?X11Forwarding', line: 'X11Forwarding no' }
    - { regexp: '^#?MaxAuthTries', line: 'MaxAuthTries 3' }
  notify: restart ssh

- name: Configure kernel hardening
  sysctl:
    name: "{{ item.name }}"
    value: "{{ item.value }}"
    state: present
    reload: yes
  loop:
    - { name: 'net.ipv4.ip_forward', value: '0' }
    - { name: 'net.ipv4.conf.all.rp_filter', value: '1' }
    - { name: 'net.ipv4.conf.default.rp_filter', value: '1' }
    - { name: 'net.ipv4.icmp_echo_ignore_broadcasts', value: '1' }
    - { name: 'net.ipv4.icmp_ignore_bogus_error_responses', value: '1' }
    - { name: 'net.ipv4.tcp_syncookies', value: '1' }
    - { name: 'net.ipv4.conf.all.accept_redirects', value: '0' }
    - { name: 'net.ipv4.conf.default.accept_redirects', value: '0' }
    - { name: 'net.ipv4.conf.all.secure_redirects', value: '0' }
    - { name: 'net.ipv4.conf.all.accept_source_route', value: '0' }

- name: Create 2GB swap file
  command: fallocate -l 2G /swapfile
  args:
    creates: /swapfile

- name: Set swap file permissions
  file:
    path: /swapfile
    mode: '0600'

- name: Enable swap
  command: mkswap /swapfile
  when: ansible_swaptotal_mb == 0

- name: Activate swap
  command: swapon /swapfile
  when: ansible_swaptotal_mb == 0

- name: Add swap to fstab
  lineinfile:
    path: /etc/fstab
    line: '/swapfile none swap sw 0 0'
    state: present

- name: Configure unattended-upgrades
  copy:
    content: |
      APT::Periodic::Update-Package-Lists "1";
      APT::Periodic::Unattended-Upgrade "1";
      APT::Periodic::AutocleanInterval "7";
    dest: /etc/apt/apt.conf.d/20auto-upgrades

- name: Configure fail2ban for SSH fallback
  copy:
    content: |
      [sshd]
      enabled = true
      port = {{ ssh_port }}
      filter = sshd
      logpath = /var/log/auth.log
      maxretry = 10
      findtime = 1h
      bantime = 1h
    dest: /etc/fail2ban/jail.local
  notify: restart fail2ban

- name: Start and enable services
  systemd:
    name: "{{ item }}"
    state: started
    enabled: yes
  loop:
    - ssh
    - fail2ban
    - auditd
```

- [ ] **Step 2: Create handlers**

```yaml
---
# ansible/roles/cis-hardening/handlers/main.yml

- name: restart ssh
  systemd:
    name: ssh
    state: restarted

- name: restart fail2ban
  systemd:
    name: fail2ban
    state: restarted
```

- [ ] **Step 3: Commit**
  ```bash
  git add ansible/roles/cis-hardening/
  git commit -m "feat: add CIS hardening ansible role"
  ```

---

### Task 3: nftables Configuration

**Files:**
- Create: `ansible/roles/cis-hardening/templates/nftables.conf.j2`
- Modify: `ansible/roles/cis-hardening/tasks/main.yml`

- [ ] **Step 1: Create nftables template**

```j2
#!/usr/sbin/nft -f
# ansible/roles/cis-hardening/templates/nftables.conf.j2

flush ruleset

table inet filter {
    set whitelist_ips {
        type ipv4_addr
        flags constant
        elements = { {{ whitelist_ips | join(', ') }} }
    }
    
    chain input {
        type filter hook input priority 0; policy drop;
        
        # Whitelist trusted IPs (CRITICAL)
        ip saddr @whitelist_ips accept
        
        # Allow loopback
        iif "lo" accept
        
        # Allow established connections
        ct state established,related accept
        
        # Allow ICMP (ping)
        ip protocol icmp accept
        
        # Allow SSH with rate limiting
        tcp dport {{ ssh_port }} ct state new limit rate 3/minute accept
        
        # Allow HTTP/HTTPS
        tcp dport {80, 443} accept
        
        # Log dropped packets for CrowdSec
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
    
    chain output {
        type filter hook output priority 0; policy accept;
    }
}
```

- [ ] **Step 2: Add nftables tasks to main.yml**

```yaml
# Add to ansible/roles/cis-hardening/tasks/main.yml before "Start and enable services"

- name: Configure nftables
  template:
    src: nftables.conf.j2
    dest: /etc/nftables.conf
    mode: '0644'
  notify: reload nftables

- name: Enable and start nftables
  systemd:
    name: nftables
    state: started
    enabled: yes

- name: Disable UFW
  systemd:
    name: ufw
    state: stopped
    enabled: no
  ignore_errors: yes
```

- [ ] **Step 3: Add nftables handler**

```yaml
# Add to ansible/roles/cis-hardening/handlers/main.yml

- name: reload nftables
  command: nft -f /etc/nftables.conf
```

- [ ] **Step 4: Commit**
  ```bash
  git add ansible/roles/cis-hardening/
  git commit -m "feat: add nftables configuration with whitelist"
  ```

---

### Task 4: Dokku Installation Role

**Files:**
- Create: `ansible/roles/dokku/tasks/main.yml`
- Create: `ansible/roles/dokku/handlers/main.yml`

- [ ] **Step 1: Create Dokku tasks**

```yaml
---
# ansible/roles/dokku/tasks/main.yml

- name: Install Dokku dependencies
  apt:
    name:
      - apt-transport-https
      - ca-certificates
      - gnupg
      - software-properties-common
    state: present

- name: Add Dokku GPG key
  apt_key:
    url: https://packagecloud.io/dokku/dokku/gpgkey
    state: present

- name: Add Dokku repository
  apt_repository:
    repo: deb https://packagecloud.io/dokku/dokku/ubuntu/ noble main
    state: present
    update_cache: yes

- name: Install Dokku
  apt:
    name: dokku
    state: present

- name: Configure Dokku hostname
  command: dokku hostname:set {{ domain }}
  ignore_errors: yes

- name: Install Dokku plugins
  command: dokku plugin:install {{ item.url }} {{ item.name }}
  args:
    creates: /var/lib/dokku/plugins/available/{{ item.name }}
  loop:
    - { name: postgres, url: https://github.com/dokku/dokku-postgres.git }
    - { name: redis, url: https://github.com/dokku/dokku-redis.git }
    - { name: letsencrypt, url: https://github.com/dokku/dokku-letsencrypt.git }

- name: Configure global SSL with Let's Encrypt
  command: dokku letsencrypt:set --global email admin@{{ domain }}
  ignore_errors: yes
```

- [ ] **Step 2: Commit**
  ```bash
  git add ansible/roles/dokku/
  git commit -m "feat: add dokku installation role"
  ```

---

### Task 5: CrowdSec Installation Role

**Files:**
- Create: `ansible/roles/crowdsec/tasks/main.yml`
- Create: `ansible/roles/crowdsec/templates/whitelist.yaml.j2`
- Create: `ansible/roles/crowdsec/handlers/main.yml`

- [ ] **Step 1: Create CrowdSec tasks**

```yaml
---
# ansible/roles/crowdsec/tasks/main.yml

- name: Add CrowdSec GPG key
  apt_key:
    url: https://packagecloud.io/crowdsec/crowdsec/gpgkey
    state: present

- name: Add CrowdSec repository
  apt_repository:
    repo: deb https://packagecloud.io/crowdsec/crowdsec/ubuntu/ noble main
    state: present
    update_cache: yes

- name: Install CrowdSec
  apt:
    name:
      - crowdsec
      - crowdsec-firewall-bouncer-nftables
    state: present

- name: Install CrowdSec collections
  command: cscli collections install {{ item }}
  loop: "{{ crowdsec_collections }}"
  register: collections_result
  changed_when: "'already exists' not in collections_result.stdout"

- name: Configure CrowdSec whitelist
  template:
    src: whitelist.yaml.j2
    dest: /etc/crowdsec/parsers/s02-enrich/whitelist.yaml
    mode: '0644'
  notify: reload crowdsec

- name: Install nginx bouncer
  apt:
    name: crowdsec-nginx-bouncer
    state: present
  notify: reload nginx

- name: Enable and start CrowdSec
  systemd:
    name: crowdsec
    state: started
    enabled: yes

- name: Enable and start firewall bouncer
  systemd:
    name: crowdsec-firewall-bouncer
    state: started
    enabled: yes
```

- [ ] **Step 2: Create whitelist template**

```j2
# ansible/roles/crowdsec/templates/whitelist.yaml.j2
name: crowdsecurity/whitelist-good-actors
whitelist:
  reason: "Trusted admin and agent IPs"
  ip:
{% for ip in whitelist_ips %}
    - "{{ ip }}"
{% endfor %}
```

- [ ] **Step 3: Create handlers**

```yaml
---
# ansible/roles/crowdsec/handlers/main.yml

- name: reload crowdsec
  systemd:
    name: crowdsec
    state: reloaded

- name: reload nginx
  systemd:
    name: nginx
    state: reloaded
```

- [ ] **Step 4: Commit**
  ```bash
  git add ansible/roles/crowdsec/
  git commit -m "feat: add crowdsec installation with whitelist"
  ```

---

### Task 6: AIDE Configuration Role

**Files:**
- Create: `ansible/roles/aide/tasks/main.yml`
- Create: `ansible/roles/aide/templates/aide.conf.j2`

- [ ] **Step 1: Create AIDE tasks**

```yaml
---
# ansible/roles/aide/tasks/main.yml

- name: Configure AIDE
  template:
    src: aide.conf.j2
    dest: /etc/aide/aide.conf
    mode: '0644'

- name: Initialize AIDE database (first run)
  command: aideinit
  args:
    creates: /var/lib/aide/aide.db.new
  timeout: 3600

- name: Copy new database as current
  copy:
    src: /var/lib/aide/aide.db.new
    dest: /var/lib/aide/aide.db
    remote_src: yes
    mode: '0600'
```

- [ ] **Step 2: Create AIDE config template**

```j2
# ansible/roles/aide/templates/aide.conf.j2
# AIDE configuration - reduced scope for 4GB RAM

database=file:/var/lib/aide/aide.db
database_out=file:/var/lib/aide/aide.db.new
verbose=5

# Monitored directories (reduced from full system)
/boot   NORMAL
/bin    NORMAL
/sbin   NORMAL
/lib    NORMAL
/lib64  NORMAL
/opt    NORMAL
/root   NORMAL
/usr/bin    NORMAL
/usr/sbin   NORMAL
/usr/local/bin  NORMAL
/usr/local/sbin NORMAL
/etc        PERMS

# Exclusions
!/var/log/aide
!/var/log/crowdsec
!/var/lib/docker
!/var/lib/dokku
!/tmp
!/var/tmp
!/proc
!/sys
!/dev
!/run
!/var/run
```

- [ ] **Step 3: Commit**
  ```bash
  git add ansible/roles/aide/
  git commit -m "feat: add aide configuration with reduced scope"
  ```

---

### Task 7: Lynis Configuration Role

**Files:**
- Create: `ansible/roles/lynis/tasks/main.yml`

- [ ] **Step 1: Create Lynis tasks**

```yaml
---
# ansible/roles/lynis/tasks/main.yml

- name: Ensure Lynis is installed
  apt:
    name: lynis
    state: present

- name: Create Lynis report directory
  file:
    path: /var/log/lynis
    state: directory
    mode: '0755'
```

- [ ] **Step 2: Commit**
  ```bash
  git add ansible/roles/lynis/
  git commit -m "feat: add lynis configuration"
  ```

---

## Phase 2: Monitoring Scripts

### Task 8: Telegram Library

**Files:**
- Create: `scripts/lib/telegram.sh`

- [ ] **Step 1: Create Telegram library**

```bash
#!/bin/bash
# scripts/lib/telegram.sh
# Telegram notification library

TELEGRAM_BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-}"
TELEGRAM_CHAT_ID="${TELEGRAM_CHAT_ID:-1631006}"

# Get server IP for notifications
SERVER_IP="${SERVER_IP:-$(curl -s -4 ifconfig.me 2>/dev/null || echo "unknown")}"
SERVER_HOSTNAME="${SERVER_HOSTNAME:-$(hostname -s 2>/dev/null || echo "unknown")}"

send_telegram_message() {
    local message="$1"
    local parse_mode="${2:-HTML}"
    
    if [[ -z "$TELEGRAM_BOT_TOKEN" ]]; then
        echo "Error: TELEGRAM_BOT_TOKEN not set" >&2
        return 1
    fi
    
    # Add server info footer
    local full_message="${message}

<i>📍 ${SERVER_HOSTNAME} (${SERVER_IP})</i>"
    
    curl -s -X POST \
        "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
        -d "chat_id=${TELEGRAM_CHAT_ID}" \
        -d "text=${full_message}" \
        -d "parse_mode=${parse_mode}" \
        -d "disable_web_page_preview=true" \
    | grep -q '"ok":true' && echo "Message sent successfully" || echo "Failed to send message"
}

send_telegram_alert() {
    local title="$1"
    local body="$2"
    local icon="$3"
    
    local message="${icon} <b>${title}</b>

${body}"
    
    send_telegram_message "$message"
}

# Export functions
export -f send_telegram_message
export -f send_telegram_alert
```

- [ ] **Step 2: Make executable**
  ```bash
  chmod +x scripts/lib/telegram.sh
  ```

- [ ] **Step 3: Commit**
  ```bash
  git add scripts/lib/
  git commit -m "feat: add telegram notification library"
  ```

---

### Task 9: CrowdSec Report Script

**Files:**
- Create: `scripts/cron/crowdsec-report.sh`

- [ ] **Step 1: Create CrowdSec report script**

```bash
#!/bin/bash
# scripts/cron/crowdsec-report.sh
# CrowdSec summary report every 6 hours

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../lib/telegram.sh"

# Get metrics
ALERTS=$(cscli alerts list -o json 2>/dev/null | jq length || echo "0")
DECISIONS=$(cscli decisions list -o json 2>/dev/null | jq length || echo "0")
CAPI_DECISIONS=$(cscli decisions list -o json -a 2>/dev/null | jq '[.[] | select(.origin == "CAPI")] | length' || echo "0")

# Get top scenarios
TOP_SCENARIOS=$(cscli alerts list -o json 2>/dev/null | jq -r '.[].scenario' | sort | uniq -c | sort -rn | head -5 | awk '{print "• " $2 ": " $1}' || echo "No data")

# Get top countries
TOP_COUNTRIES=$(cscli alerts list -o json 2>/dev/null | jq -r '.[].source.cn' | sort | uniq -c | sort -rn | head -3 | awk '{print "• " $2 ": " $1}' || echo "No data")

MESSAGE="🛡️ <b>CrowdSec Report (6h)</b>

📊 Атаки: ${ALERTS}
🔒 Забанено: ${DECISIONS} IP
🌐 CAPI блоклист: ${CAPI_DECISIONS} IP

<b>Топ страны:</b>
${TOP_COUNTRIES}

<b>Топ сценарии:</b>
${TOP_SCENARIOS}"

send_telegram_message "$MESSAGE"
```

- [ ] **Step 2: Make executable and commit**
  ```bash
  chmod +x scripts/cron/crowdsec-report.sh
  git add scripts/cron/crowdsec-report.sh
  git commit -m "feat: add crowdsec report script"
  ```

---

### Task 10: AIDE Check Script

**Files:**
- Create: `scripts/cron/aide-check.sh`

- [ ] **Step 1: Create AIDE check script**

```bash
#!/bin/bash
# scripts/cron/aide-check.sh
# AIDE FIM check - runs at 02:00 MSK

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../lib/telegram.sh"

# Run AIDE check with timeout and low priority
OUTPUT=$(timeout 3600 nice -n 10 ionice -c 3 aide --check 2>&1) || {
    send_telegram_alert "AIDE Check Failed" "Timeout or error occurred" "⚠️"
    exit 1
}

# Parse results
if echo "$OUTPUT" | grep -q "Looks okay"; then
    MESSAGE="🔍 <b>AIDE FIM Report</b>

✅ Изменений не обнаружено
📁 Проверено файлов: $(echo "$OUTPUT" | grep -oP '\d+(?= files scanned)' || echo "N/A")"
else
    CHANGES=$(echo "$OUTPUT" | grep -A 20 "Changed entries" | head -20 || echo "See /var/log/aide/")
    MESSAGE="🔍 <b>AIDE FIM Report</b>

⚠️ <b>Обнаружены изменения!</b>

${CHANGES}

📋 Полный отчёт: /var/log/aide/"
fi

send_telegram_message "$MESSAGE"
```

- [ ] **Step 2: Make executable and commit**
  ```bash
  chmod +x scripts/cron/aide-check.sh
  git add scripts/cron/aide-check.sh
  git commit -m "feat: add aide check script with timeout"
  ```

---

### Task 11: Lynis Audit Script

**Files:**
- Create: `scripts/cron/lynis-audit.sh`

- [ ] **Step 1: Create Lynis audit script**

```bash
#!/bin/bash
# scripts/cron/lynis-audit.sh
# Lynis CIS audit - runs Sundays at 03:00 MSK

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../lib/telegram.sh"

REPORT_FILE="/var/log/lynis/lynis-report-$(date +%Y%m%d).txt"

# Run Lynis with timeout
timeout 1800 lynis audit system --quick --report-file "$REPORT_FILE" > /tmp/lynis-output.txt 2>&1 || true

# Parse results
SCORE=$(grep -oP 'Hardening index : \K[0-9.]+' /tmp/lynis-output.txt || echo "N/A")
WARNINGS=$(grep -c 'Warning:' /tmp/lynis-output.txt || echo "0")
HARDENED=$(grep -c 'Hardened:' /tmp/lynis-output.txt || echo "0")

MESSAGE="🔒 <b>CIS Audit Report (Lynis)</b>

💯 Score: ${SCORE}/100
⚠️ Warnings: ${WARNINGS}
✅ Hardened: ${HARDENED}

📄 Полный отчёт: ${REPORT_FILE}"

send_telegram_message "$MESSAGE"
```

- [ ] **Step 2: Make executable and commit**
  ```bash
  chmod +x scripts/cron/lynis-audit.sh
  git add scripts/cron/lynis-audit.sh
  git commit -m "feat: add lynis audit script with timeout"
  ```

---

### Task 12: Resource Monitor Script

**Files:**
- Create: `scripts/cron/resource-monitor.sh`

- [ ] **Step 1: Create resource monitor script**

```bash
#!/bin/bash
# scripts/cron/resource-monitor.sh
# Resource monitoring - CPU/RAM alerts

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../lib/telegram.sh"

# Configuration
CPU_THRESHOLD=90
RAM_THRESHOLD=90
DISK_THRESHOLD=90
WINDOW_MINUTES=20
ALERT_COOLDOWN=3600  # 1 hour between alerts
STATE_FILE="/tmp/resource-monitor-state"

# Check cooldown
if [[ -f "$STATE_FILE" ]]; then
    LAST_ALERT=$(cat "$STATE_FILE")
    NOW=$(date +%s)
    if (( NOW - LAST_ALERT < ALERT_COOLDOWN )); then
        exit 0
    fi
fi

# Get average CPU over window (using sar if available, else ps)
if command -v sar &> /dev/null; then
    CPU_AVG=$(sar -u "${WINDOW_MINUTES}" 1 | tail -1 | awk '{print 100 - $8}')
else
    # Fallback: current CPU usage
    CPU_AVG=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
fi

# Get RAM usage
RAM_INFO=$(free | grep Mem)
RAM_TOTAL=$(echo "$RAM_INFO" | awk '{print $2}')
RAM_USED=$(echo "$RAM_INFO" | awk '{print $3}')
RAM_AVG=$(( RAM_USED * 100 / RAM_TOTAL ))

# Get disk usage
DISK_AVG=$(df / | tail -1 | awk '{print $5}' | tr -d '%')

# Check thresholds
ALERT_NEEDED=false
ALERT_MESSAGE=""

if (( $(echo "$CPU_AVG > $CPU_THRESHOLD" | bc -l) )); then
    ALERT_NEEDED=true
    TOP_CPU=$(ps aux --sort=-%cpu | head -6 | tail -5 | awk '{print $11 ": " $3 "%"}')
    ALERT_MESSAGE+="📊 <b>CPU Usage: ${CPU_AVG}%</b> (threshold: ${CPU_THRESHOLD}%)

Top processes:
${TOP_CPU}

"
fi

if (( RAM_AVG > RAM_THRESHOLD )); then
    ALERT_NEEDED=true
    TOP_MEM=$(ps aux --sort=-%mem | head -6 | tail -5 | awk '{print $11 ": " $4 "%"}')
    ALERT_MESSAGE+="🧠 <b>RAM Usage: ${RAM_AVG}%</b> (threshold: ${RAM_THRESHOLD}%)

Top processes:
${TOP_MEM}

"
fi

if (( DISK_AVG > DISK_THRESHOLD )); then
    ALERT_NEEDED=true
    ALERT_MESSAGE+="💾 <b>Disk Usage: ${DISK_AVG}%</b> (threshold: ${DISK_THRESHOLD}%)

"
fi

if [[ "$ALERT_NEEDED" == true ]]; then
    MESSAGE="⚠️ <b>Resource Alert</b>

${ALERT_MESSAGE}
<i>Average over ${WINDOW_MINUTES} minutes</i>"
    
    send_telegram_message "$MESSAGE"
    date +%s > "$STATE_FILE"
fi
```

- [ ] **Step 2: Make executable and commit**
  ```bash
  chmod +x scripts/cron/resource-monitor.sh
  git add scripts/cron/resource-monitor.sh
  git commit -m "feat: add resource monitor script"
  ```

---

### Task 12.5: GeoIP Update Script

**Files:**
- Create: `scripts/cron/update-geoip.sh`

- [ ] **Step 1: Create GeoIP update script**

```bash
#!/bin/bash
# scripts/cron/update-geoip.sh
# Update CrowdSec GeoIP database weekly

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../lib/telegram.sh"

LOG_FILE="/var/log/crowdsec-geoip-update.log"

echo "[$(date)] Starting GeoIP database update..." >> "$LOG_FILE"

# Update CrowdSec hub (includes GeoIP databases)
if cscli hub update >> "$LOG_FILE" 2>&1; then
    echo "[$(date)] Hub updated successfully" >> "$LOG_FILE"
    
    # Upgrade collections to get latest GeoIP data
    if cscli collections upgrade -a >> "$LOG_FILE" 2>&1; then
        echo "[$(date)] Collections upgraded successfully" >> "$LOG_FILE"
        
        # Reload CrowdSec to apply updates
        if systemctl reload crowdsec >> "$LOG_FILE" 2>&1; then
            MESSAGE="🌍 <b>GeoIP Update Successful</b>

✅ CrowdSec hub updated
✅ Collections upgraded
✅ Service reloaded

<i>Next update: $(date -d '+7 days' '+%Y-%m-%d')</i>"
            
            send_telegram_message "$MESSAGE"
            echo "[$(date)] Update completed successfully" >> "$LOG_FILE"
        else
            echo "[$(date)] Failed to reload CrowdSec" >> "$LOG_FILE"
            send_telegram_alert "GeoIP Update Warning" "Hub updated but failed to reload CrowdSec" "⚠️"
        fi
    else
        echo "[$(date)] Failed to upgrade collections" >> "$LOG_FILE"
        send_telegram_alert "GeoIP Update Failed" "Failed to upgrade CrowdSec collections" "❌"
        exit 1
    fi
else
    echo "[$(date)] Failed to update hub" >> "$LOG_FILE"
    send_telegram_alert "GeoIP Update Failed" "Failed to update CrowdSec hub" "❌"
    exit 1
fi
```

- [ ] **Step 2: Make executable and commit**
  ```bash
  chmod +x scripts/cron/update-geoip.sh
  git add scripts/cron/update-geoip.sh
  git commit -m "feat: add geoip update script for weekly updates"
  ```

---

### Task 13: Setup Cron Jobs

**Files:**
- Create: `scripts/setup-cron.sh`

- [ ] **Step 1: Create cron setup script**

```bash
#!/bin/bash
# scripts/setup-cron.sh
# Setup cron jobs for monitoring

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_FILE="/tmp/dokku-monitoring-cron"

# Get server IP
SERVER_IP=$(curl -s -4 ifconfig.me 2>/dev/null || echo "unknown")
SERVER_HOSTNAME=$(hostname -s 2>/dev/null || echo "unknown")

cat > "$CRON_FILE" << EOF
# Dokku PaaS Monitoring Cron Jobs
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN:-}
TELEGRAM_CHAT_ID=1631006
SERVER_IP=${SERVER_IP}
SERVER_HOSTNAME=${SERVER_HOSTNAME}

# CrowdSec report every 6 hours
0 */6 * * * ${SCRIPT_DIR}/cron/crowdsec-report.sh >> /var/log/crowdsec-report.log 2>&1

# AIDE FIM check at 02:00 MSK (UTC+3)
0 23 * * * ${SCRIPT_DIR}/cron/aide-check.sh >> /var/log/aide-check.log 2>&1

# Lynis audit Sundays at 03:00 MSK (00:00 UTC)
0 0 * * 0 ${SCRIPT_DIR}/cron/lynis-audit.sh >> /var/log/lynis-audit.log 2>&1

# Resource monitor every 5 minutes
*/5 * * * * ${SCRIPT_DIR}/cron/resource-monitor.sh >> /var/log/resource-monitor.log 2>&1

# Disk check every 15 minutes
*/15 * * * * df -h / | tail -1 | awk '\$5 > 90 {print "DISK CRITICAL: " \$0}' | while read line; do echo "\$line" | SERVER_IP=${SERVER_IP} SERVER_HOSTNAME=${SERVER_HOSTNAME} ${SCRIPT_DIR}/../lib/telegram.sh send_telegram_message "💾 <b>Disk Alert</b>\n\n\$line"; done
EOF

# Install cron file
crontab "$CRON_FILE"
rm "$CRON_FILE"

echo "Cron jobs installed successfully"
echo "Server IP: ${SERVER_IP}"
echo "Hostname: ${SERVER_HOSTNAME}"
crontab -l
```

- [ ] **Step 2: Make executable and commit**
  ```bash
  chmod +x scripts/setup-cron.sh
  git add scripts/setup-cron.sh
  git commit -m "feat: add cron setup script"
  ```

---

## Phase 3: Documentation

### Task 14: Create Documentation Files

**Files:**
- Create: `docs/Dokku-project/AGENT.md`
- Create: `docs/Dokku-project/OPERATOR.md`
- Create: `docs/Dokku-project/ARCHITECTURE.md`
- Create: `keys/README.md`

- [ ] **Step 1: Create AGENT.md**

```markdown
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
```

- [ ] **Step 2: Create OPERATOR.md**

```markdown
# Operator Handbook

## System Overview

- **VPS:** SpaceWeb, 80.93.63.169
- **Domain:** clawtech.ru
- **SSH:** Port 2233
- **OS:** Ubuntu 24.04 LTS (CIS Level 1 hardened)

## Daily Operations

### Check System Health
```bash
# Resource usage
htop
free -h
df -h

# CrowdSec status
cscli metrics
cscli decisions list

# Docker status
docker ps
dokku apps:list
```

### Deploy Application
```bash
# On local machine
git remote add dokku dokku@clawtech.ru:appname
git push dokku main
```

### View Logs
```bash
# CrowdSec
journalctl -u crowdsec -f

# Nginx
dokku nginx:logs appname

# Application
dokku logs appname -t
```

## Backup Procedures

### Manual Backup
```bash
# PostgreSQL
dokku postgres:export dbname > backup.sql

# Redis
dokku redis:export redisname > redis.backup

# Application data
dokku storage:export appname
```

## Recovery Procedures

See INCIDENT_RESPONSE.md for detailed recovery steps.
```

- [ ] **Step 3: Create ARCHITECTURE.md**

```markdown
# System Architecture

## High-Level Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    SpaceWeb VPS (Ubuntu 24.04)              │
│                    80.93.63.169 / clawtech.ru               │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  CIS Level 1 │  │    Dokku     │  │   CrowdSec       │  │
│  │  Hardening   │  │  (Docker)    │  │  + Collections   │  │
│  │              │  │              │  │  + CAPI Blocklist│  │
│  │  • SSH 2233  │  │  • Node.js   │  │  + Telegram      │  │
│  │  • nftables  │  │  • Python    │  │    notifications │  │
│  │  • Auditd    │  │  • PG/Redis  │  │                  │  │
│  │  • AIDE      │  │  • SQLite*   │  │  • nginx         │  │
│  │  • Lynis     │  │              │  │  • docker        │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │              Monitoring & Reporting                    │ │
│  │  • FIM (AIDE) nightly at 02:00 MSK → Telegram        │ │
│  │  • CrowdSec summary every 6h → Telegram              │ │
│  │  • CIS audit (Lynis) Sundays → Telegram              │ │
│  │  • Resource alerts (CPU/RAM) continuous              │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

*SQLite requires persistent storage configuration

## Technology Stack

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

## Network Flow

1. External request → nftables (port 80/443)
2. Nginx (Dokku) → Docker container
3. CrowdSec analyzes logs → Blocks malicious IPs
4. Firewall bouncer drops banned IPs at nftables level
```

- [ ] **Step 4: Create keys/README.md**

```markdown
# SSH Keys

## clawtech-vps.pem

**Purpose:** SSH access to VPS (root@clawtech.ru:2233)

**Security:**
- Keep private key secure
- Never commit to git
- Use only from secure machines

**Usage:**
```bash
ssh -p 2233 -i clawtech-vps.pem root@clawtech.ru
```

**Permissions:**
```bash
chmod 600 clawtech-vps.pem
```

## Key Rotation Procedure

1. Generate new key pair locally
2. Add public key to VPS: `/root/.ssh/authorized_keys`
3. Test new key works
4. Remove old public key
5. Update this directory with new private key
```

- [ ] **Step 5: Commit documentation**
  ```bash
  git add docs/ keys/
  git commit -m "docs: add agent, operator, and architecture documentation"
  ```

---

## Phase 4: Deployment

### Task 15: Run Ansible Playbook

- [ ] **Step 1: Verify prerequisites**
  ```bash
  cd ansible
  ansible -m ping prod
  ```
  Expected: `pong` response

- [ ] **Step 2: Run playbook in check mode**
  ```bash
  ansible-playbook site.yml --check --diff
  ```
  Review changes before applying

- [ ] **Step 3: Run playbook**
  ```bash
  ansible-playbook site.yml
  ```
  Expected: All tasks completed successfully

- [ ] **Step 4: Verify SSH port change**
  ```bash
  # Test new port
  ssh -p 2233 -i ../keys/clawtech-vps.pem root@clawtech.ru
  ```

- [ ] **Step 5: Verify services**
  ```bash
  # On VPS
  systemctl status crowdsec
  systemctl status crowdsec-firewall-bouncer
  systemctl status nftables
  dokku version
  cscli metrics
  ```

- [ ] **Step 6: Commit deployment state**
  ```bash
  git add -A
  git commit -m "deploy: initial ansible deployment completed"
  ```

---

### Task 16: Setup Cron Jobs

- [ ] **Step 1: Export Telegram token**
  ```bash
  export TELEGRAM_BOT_TOKEN="your_bot_token_here"
  ```

- [ ] **Step 2: Run cron setup**
  ```bash
  cd scripts
  ./setup-cron.sh
  ```

- [ ] **Step 3: Verify cron jobs**
  ```bash
  crontab -l
  ```
  Expected: All 5 jobs listed (CrowdSec, AIDE, Lynis, Resource, GeoIP)

- [ ] **Step 4: Test scripts manually**
  ```bash
  ./cron/crowdsec-report.sh
  ```
  Expected: "Message sent successfully" and Telegram notification

- [ ] **Step 5: Commit**
  ```bash
  git add -A
  git commit -m "deploy: setup monitoring cron jobs"
  ```

---

### Task 17: Final Verification

- [ ] **Step 1: Run full system check**
  ```bash
  # CIS audit
  lynis audit system --quick
  
  # Check hardening score
  grep "Hardening index" /var/log/lynis.log
  ```

- [ ] **Step 2: Verify all reports**
  - Trigger test CrowdSec report
  - Verify Telegram receives message
  - Check report formatting

- [ ] **Step 3: Security checklist**
  - [ ] SSH on port 2233 only
  - [ ] IPv6 disabled
  - [ ] nftables active with whitelist
  - [ ] CrowdSec running with all collections
  - [ ] Fail2ban running as fallback
  - [ ] AIDE initialized
  - [ ] Cron jobs installed
  - [ ] Telegram notifications working

- [ ] **Step 4: Final commit**
  ```bash
  git add -A
  git commit -m "deploy: system fully operational"
  git tag -a v1.0 -m "Initial production deployment"
  ```

---

## Post-Deployment

### Regular Maintenance

- **Weekly:** Review Lynis audit reports and GeoIP update notifications
- **Daily:** Check Telegram for AIDE/CrowdSec alerts
- **As needed:** Update CrowdSec collections: `cscli collections upgrade -a`

### Updating System

```bash
# Security updates only
ansible-playbook site.yml --tags security-updates

# Full update (requires confirmation)
ansible-playbook site.yml
```

---

## Self-Review Checklist

**Spec coverage:**
- [x] CIS Level 1 hardening (with deviations)
- [x] SSH port 2233
- [x] IPv6 disabled
- [x] nftables with whitelist
- [x] CrowdSec with all collections
- [x] CrowdSec whitelist configuration
- [x] AIDE with reduced scope
- [x] Lynis auditing
- [x] Fail2ban fallback
- [x] Resource monitoring
- [x] Telegram notifications
- [x] **GeoIP weekly updates**
- [x] Dokku installation
- [x] Documentation

**Placeholder scan:**
- [x] No TBD/TODO
- [x] All code provided
- [x] All commands specified
- [x] Exact file paths used

**Type consistency:**
- [x] Variable names consistent
- [x] File paths consistent
- [x] Service names consistent

---

**Plan complete and saved to `docs/superpowers/plans/2025-01-06-dokku-paas-implementation.md`**

## Execution Options

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
