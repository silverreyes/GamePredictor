# VPS Deployment Guide

Deploy NFL Game Predictor to a Hostinger VPS at nostradamus.silverreyes.net

## Prerequisites

- Ubuntu VPS with root/sudo access
- Domain DNS managed via Hostinger panel
- Existing VPS nginx serving other sites (do NOT touch existing server blocks)

## Step 1: Install Docker

```sh
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker
sudo apt-get install -y docker-compose-plugin
```

Verify: `docker compose version`

## Step 2: Clone repository

```sh
git clone https://github.com/NatoJenkins/GamePredictor.git
cd GamePredictor
```

## Step 3: Configure environment

```sh
cp .env.example .env
```

Then edit `.env` and set real values for `POSTGRES_PASSWORD` and `RELOAD_TOKEN`. `REFRESH_CRON_HOUR` defaults to 6 (Tuesday 6 AM UTC).

## Step 4: Get VPS IP for DNS

```sh
curl -4 ifconfig.me
```

Note the IP address for the next step.

## Step 5: Configure DNS

In Hostinger DNS panel, add an A record:

- Name: `nostradamus`
- Points to: `<VPS IP from step 4>`
- TTL: default

Wait for DNS propagation before proceeding (check with `dig nostradamus.silverreyes.net`).

## Step 6: Add VPS nginx server block

```sh
sudo cp docs/vps-nginx-block.conf /etc/nginx/sites-available/nostradamus.silverreyes.net
sudo ln -s /etc/nginx/sites-available/nostradamus.silverreyes.net /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

## Step 7: SSL with Certbot

```sh
sudo certbot --nginx -d nostradamus.silverreyes.net
```

Certbot modifies the server block to add SSL. The app's nginx container remains plain HTTP on port 8080 internally.

## Step 8: Start services

```sh
docker compose up -d
```

Services start in order: postgres (init.sql creates schema) -> api (loads model from seeded volume) -> worker (APScheduler) -> nginx (builds frontend).

First build takes several minutes (npm install + pip install).

Verify: `docker compose ps` shows all 4 services healthy.

## Step 9: First data run (interactive)

```sh
docker compose exec worker python -m pipeline.refresh
```

This is the initial 20-season data ingestion. Takes ~30 minutes. Watch for errors -- do NOT background this.

After completion, visit `https://nostradamus.silverreyes.net` to verify the dashboard loads.

## Ongoing Operations

- Weekly refresh runs automatically (Tuesday 6 AM UTC via APScheduler in worker)
- After retrain, approve new model: `curl -X POST https://nostradamus.silverreyes.net/api/model/reload -H "Authorization: Bearer <RELOAD_TOKEN>"`
- View logs: `docker compose logs -f worker`
- Rebuild after code changes: `git pull && docker compose up -d --build`
