# Hello World - Dokku Deployment Test

Simple Node.js application to test Dokku deployment process.

## Quick Start

```bash
# 1. Initialize git
git init
git add .
git commit -m "Initial commit"

# 2. Add Dokku remote
git remote add dokku dokku@clawtech.ru:hello-world

# 3. Deploy
git push dokku main

# 4. Check deployment
curl https://hello-world.clawtech.ru
```

## Expected Output

```json
{
  "message": "Hello from Dokku!",
  "timestamp": "2026-04-07T17:35:00.000Z",
  "server": "clawtech.ru",
  "platform": "Dokku PaaS",
  "version": "1.0.0"
}
```

## Endpoints

- `GET /` - Main endpoint returning hello message
- `GET /health` - Health check endpoint

## Troubleshooting

### Deployment fails

```bash
# Check logs
dokku logs hello-world -n 100

# Check app status
dokku ps:report hello-world

# Rebuild
dokku ps:rebuild hello-world
```

### 502 Bad Gateway

The app may not be binding to the correct port. Ensure `process.env.PORT` is used.

