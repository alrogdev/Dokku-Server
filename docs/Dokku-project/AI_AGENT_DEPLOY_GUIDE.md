# AI Agent Developer Guide: Deploying to Dokku Server

**Project:** clawtech.ru Dokku PaaS  
**Server:** 80.93.63.169 (SpaceWeb VPS)  
**Domain:** clawtech.ru / *.clawtech.ru  
**SSH Port:** 2233  
**Last Updated:** 2025-01-06

---

## Quick Start

### 1. Prerequisites

Before deploying, ensure you have:
- [ ] SSH access to the server (see TOOLS.md for keys)
- [ ] Application code ready for deployment
- [ ] Git initialized in your project

### 2. Deploy in 3 Steps

```bash
# Step 1: Add Dokku remote
git remote add dokku dokku@clawtech.ru:your-app-name

# Step 2: Push to deploy
git push dokku main

# Step 3: Check deployment
dokku ps:report your-app-name
```

---

## Deployment Methods

### Method A: Standard Git Push (Recommended)

For Node.js, Python, Ruby, Go, PHP applications with standard buildpacks.

```bash
# From your project directory
git remote add dokku dokku@clawtech.ru:myapp
git push dokku main

# Dokku will automatically:
# - Detect buildpack (Node.js, Python, etc.)
# - Build Docker image
# - Deploy container
# - Configure nginx
# - Obtain SSL certificate
```

**Supported Buildpacks:**
- Node.js (package.json)
- Python (requirements.txt or Pipfile)
- Ruby (Gemfile)
- Go (go.mod)
- PHP (composer.json)
- Static sites (index.html)

---

### Method B: Dockerfile Deployment

For custom Docker builds.

```bash
# Create Dockerfile in project root
cat > Dockerfile << 'EOF'
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
CMD ["node", "server.js"]
EOF

# Deploy
git add Dockerfile
git commit -m "Add Dockerfile"
git push dokku main
```

---

### Method C: Docker Image Deployment

For pre-built images from CI/CD.

```bash
# Build and push to registry
docker build -t myregistry.com/myapp:v1.0 .
docker push myregistry.com/myapp:v1.0

# Deploy on server
ssh -p 2233 dokku-deploy@clawtech.ru \
  "dokku git:from-image myapp myregistry.com/myapp:v1.0"
```

---

## Application Configuration

### Environment Variables

```bash
# Set environment variables
dokku config:set myapp NODE_ENV=production
dokku config:set myapp DATABASE_URL=postgres://...
dokku config:set myapp API_KEY=secret

# View all config
dokku config:show myapp
```

### Persistent Storage

For file uploads, logs, SQLite:

```bash
# Create storage directory
dokku storage:ensure-directory myapp

# Mount to container
dokku storage:mount myapp /var/lib/dokku/data/storage/myapp:/app/data

# In your app, use /app/data for persistent files
```

**Note:** Without persistent storage, data is lost on rebuild!

---

## Database Setup

### PostgreSQL

```bash
# Create database
dokku postgres:create myapp-db

# Link to app
dokku postgres:link myapp-db myapp

# Get connection string
dokku postgres:info myapp-db
```

### Redis

```bash
# Create Redis instance
dokku redis:create myapp-cache

# Link to app
dokku redis:link myapp-cache myapp
```

### SQLite

```bash
# Use persistent storage for SQLite
dokku storage:ensure-directory myapp
dokku storage:mount myapp /var/lib/dokku/data/storage/myapp:/app/data

# In your app: /app/data/database.db
```

---

## Domain & SSL

### Custom Domain

```bash
# Add domain
dokku domains:set myapp myapp.clawtech.ru

# Or use root domain for main app
dokku domains:set myapp clawtech.ru
```

### SSL Certificate

```bash
# Enable Let's Encrypt (auto-renewal)
dokku letsencrypt:enable myapp

# Check certificate
dokku letsencrypt:list
```

---

## Monitoring & Logs

### View Logs

```bash
# Real-time logs
dokku logs myapp -t

# Last 100 lines
dokku logs myapp -n 100

# Nginx logs
dokku nginx:logs myapp
```

### Check Status

```bash
# App status
dokku ps:report myapp

# Resource usage
dokku ps:scale myapp web=2  # Scale to 2 instances
```

---

## Common Operations

### Restart App

```bash
dokku ps:restart myapp
```

### Rebuild App

```bash
dokku ps:rebuild myapp
```

### Stop App

```bash
dokku ps:stop myapp
```

### Delete App

```bash
# ⚠️ WARNING: This deletes everything!
dokku apps:destroy myapp
```

---

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

### Port Issues

```bash
# Check which port app uses
dokku proxy:ports myapp

# Map port (if needed)
dokku proxy:ports-add myapp http:80:3000
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

## Example: Deploy Node.js App

```bash
# 1. Prepare app
cd my-node-app
cat > package.json << 'EOF'
{
  "name": "myapp",
  "version": "1.0.0",
  "scripts": {
    "start": "node server.js"
  },
  "dependencies": {
    "express": "^4.18.0"
  }
}
EOF

# 2. Create server.js
cat > server.js << 'EOF'
const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

app.get('/', (req, res) => {
  res.json({ message: 'Hello from Dokku!' });
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
EOF

# 3. Initialize git
git init
git add .
git commit -m "Initial commit"

# 4. Deploy
git remote add dokku dokku@clawtech.ru:myapp
git push dokku main

# 5. Check
curl https://myapp.clawtech.ru
```

---

## Example: Deploy Python App

```bash
cd my-python-app

# requirements.txt
flask==2.3.0
gunicorn==21.2.0

# app.py
from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello from Flask!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

# Deploy
git init && git add . && git commit -m "init"
git remote add dokku dokku@clawtech.ru:myapp
git push dokku main
```

---

## Example: Deploy Static Site

```bash
cd my-static-site

# Create index.html
cat > index.html << 'EOF'
<!DOCTYPE html>
<html>
<head><title>My Site</title></head>
<body><h1>Hello World!</h1></body>
</html>
EOF

# Create .static file to force static buildpack
touch .static

# Deploy
git init && git add . && git commit -m "init"
git remote add dokku dokku@clawtech.ru:mysite
git push dokku main
```

---

## Useful Commands Reference

| Command | Description |
|---------|-------------|
| `dokku apps:list` | List all apps |
| `dokku ps:report <app>` | Check app status |
| `dokku logs <app> -t` | Stream logs |
| `dokku config:show <app>` | Show environment variables |
| `dokku ps:restart <app>` | Restart app |
| `dokku ps:rebuild <app>` | Rebuild and deploy |
| `dokku enter <app>` | Enter running container |
| `dokku run <app> <cmd>` | Run one-off command |

---

## Support & Resources

- **Dokku Docs:** http://dokku.viewdocs.io/dokku/
- **Server Admin:** @Rogdev (Telegram: @Rogdev_Sec_alert_bot)
- **Emergency:** Use SpaceWeb VNC console if SSH fails

---

## Quick Checklist Before Deploy

- [ ] App runs locally
- [ ] All dependencies in package.json/requirements.txt/etc
- [ ] PORT environment variable used
- [ ] .env file not committed (use config:set instead)
- [ ] Database connection uses environment variables
- [ ] Static assets properly handled

**Ready to deploy?** Run: `git push dokku main`
