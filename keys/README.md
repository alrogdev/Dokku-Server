# SSH Keys for Dokku PaaS

**⚠️ IMPORTANT:** Private keys are stored outside this repository for security.

---

## Root Access (clawtech-vps)

**User:** root  
**Host:** clawtech.ru  
**Port:** 2233  
**Key Location:** `.opencode/private/PETS-keys` (outside git)  
**Symlink:** `keys/clawtech-vps.pem` → `../.opencode/private/PETS-keys`

### Usage

```bash
# Via symlink
ssh -p 2233 -i keys/clawtech-vps.pem root@clawtech.ru

# Or directly from private location
ssh -p 2233 -i .opencode/private/PETS-keys root@clawtech.ru
```

### Permissions

```bash
chmod 600 keys/clawtech-vps.pem
```

---

## Dokku-Deploy Access

**User:** dokku-deploy  
**Host:** clawtech.ru  
**Port:** 2233  
**Key Location:** `keys/dokku-deploy/id_ed25519` (auto-generated, in git)

### Usage

```bash
# For deployment
ssh -p 2233 -i keys/dokku-deploy/id_ed25519 dokku-deploy@clawtech.ru

# Or add to ssh-agent
ssh-add keys/dokku-deploy/id_ed25519
git push dokku main
```

---

## Security Notes

- **Root key (PETS-keys):** Stored in `.opencode/private/` (never in git)
- **Dokku-deploy key:** Auto-generated, passphrase-less for CI/CD
- **Never commit private keys to git**
- **Use passphrase for root key** (already set by you)
- **Restrict root key access** (only from trusted IPs)

---

## Key Generation (if needed)

### For root access (you already have):
```bash
# Your keys are already in .opencode/private/
# Symlinks created automatically
```

### For dokku-deploy (auto-generated):
```bash
ssh-keygen -t ed25519 -f keys/dokku-deploy/id_ed25519 -N "" -C "dokku-deploy@clawtech.ru"
```

---

## Troubleshooting

### Permission denied
```bash
# Check permissions
ls -la keys/
# Should be: -rw------- (600) for private keys

# Fix permissions
chmod 600 keys/clawtech-vps.pem
chmod 600 keys/dokku-deploy/id_ed25519
```

### Key not found
```bash
# Verify symlinks
ls -la keys/clawtech-vps.pem
# Should point to: ../.opencode/private/PETS-keys

# If broken, recreate:
cd keys && ln -sf ../.opencode/private/PETS-keys clawtech-vps.pem
```
