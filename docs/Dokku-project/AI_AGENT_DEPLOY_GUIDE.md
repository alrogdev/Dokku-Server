## Troubleshooting

### Deployment Fails

```bash
# Check build logs
git push dokku main 2>&1 | tee deploy.log

# Check app logs
dokku logs myapp -n 200

# Check nginx error
dokku nginx:logs myapp
```

### SSH Connection Issues

If you can't connect to dokku@clawtech.ru:

```bash
# Check if your SSH key is added
cat ~/.ssh/id_ed25519.pub | ssh -p 2233 root@clawtech.ru "cat >> /home/dokku/.ssh/authorized_keys"

# Or use the dokku-deploy key
ssh -p 2233 -i /path/to/dokku-deploy/id_ed25519 dokku@clawtech.ru
```

### Git Push Rejected - "pre-receive hook declined"

**Problem:** Dokku expects `master` branch but you're pushing `main`

**Solution:**
```bash
# Option 1: Push main to master
git push dokku main:master --force

# Option 2: Rename local branch to master
git branch -m master
git push dokku master --force
```

### SSL Certificate Issues

```bash
# Check SSL status
dokku letsencrypt:report myapp

# Re-enable SSL if needed
dokku letsencrypt:enable myapp

# Force renew certificate
dokku letsencrypt:auto-renew
```

### App Not Accessible (502 Bad Gateway)

```bash
# Check if app is running
dokku ps:report myapp

# Check which port app uses
dokku proxy:ports myapp

# Check logs for startup errors
dokku logs myapp -n 100

# Restart app
dokku ps:restart myapp
```

### Memory Issues

```bash
# Check memory usage
dokku ps:report myapp

# Increase memory limit
dokku resource:limit memory myapp 512M
```

---

## Security Best Practices

### 1. Environment Variables
- Never commit secrets to git
- Use `dokku config:set` for all sensitive data

### 2. Database Security
- Use `dokku postgres:create` (not external DB)
- Database is not exposed to internet by default

### 3. File Permissions
- Persistent storage is owned by dokku user
- Don't run containers as root

### 4. Updates
- Regularly update base images
- Monitor security alerts from CrowdSec

---