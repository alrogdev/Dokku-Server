# SSH Keys for Dokku PaaS

## clawtech-vps.pem

**Purpose:** SSH access to VPS as root (port 2233)

**Owner:** You generate and provide this key

**Usage:**
```bash
ssh -p 2233 -i keys/clawtech-vps.pem root@clawtech.ru
```

**Permissions:**
```bash
chmod 600 keys/clawtech-vps.pem
```

---

## dokku-deploy/ Directory

Contains SSH keys for dokku-deploy user (automated deployment).

**Files:**
- `id_ed25519` - Private key (generated automatically)
- `id_ed25519.pub` - Public key (generated automatically)

**Usage for deployment:**
```bash
# Add to ssh-agent
ssh-add keys/dokku-deploy/id_ed25519

# Or specify directly
git push dokku main
```

---

## Key Generation Instructions

### For root access (you generate):
```bash
ssh-keygen -t ed25519 -f clawtech-vps -C "root@clawtech.ru"
# Enter passphrase (recommended) or leave empty
# Provide private key (clawtech-vps) to this project
# Keep public key (clawtech-vps.pub) for reference
```

### For dokku-deploy (auto-generated):
Already generated in `dokku-deploy/` directory.

---

## Security Notes

- Never commit private keys to git
- Keep `.pem` and `id_ed25519` files secure
- Use passphrase for root key (clawtech-vps)
- dokku-deploy key can be without passphrase for CI/CD
