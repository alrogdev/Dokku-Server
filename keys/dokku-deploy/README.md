# Dokku-Deploy SSH Keys

**Generated:** Automatically for dokku-deploy user

**Purpose:** Deployment and Dokku management (no sudo required)

## Files

- `id_ed25519` - Private key (KEEP SECURE)
- `id_ed25519.pub` - Public key (install on server)

## Fingerprint

```
SHA256:tiAo6vOTO9kcEWX4Ld7BZq84A6KcY41EFbVrhRtBynU dokku-deploy@clawtech.ru
```

## Usage

### Add to SSH agent:
```bash
ssh-add keys/dokku-deploy/id_ed25519
```

### Deploy application:
```bash
cd myapp
git remote add dokku dokku@clawtech.ru:myapp
git push dokku main
```

### Manual server access:
```bash
ssh -p 2233 -i keys/dokku-deploy/id_ed25519 dokku-deploy@clawtech.ru
```

## Server Setup

Ansible will automatically:
1. Create `dokku-deploy` user
2. Add `id_ed25519.pub` to `~dokku-deploy/.ssh/authorized_keys`
3. Add user to `dokku` group

## Security

- This key has NO PASSPHRASE (for automated deployment)
- Only Dokku commands allowed (no sudo)
- Keep private key secure and never commit to git
