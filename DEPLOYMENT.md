# 🚀 Serverga Deploy Qilish Yo'riqnomasi

Bu loyihani serverga deploy qilish uchun DevOps mutaxassis uchun to'liq yo'riqnoma.

## 📋 Loyiha Ma'lumotlari

**Loyiha nomi:** Sartaroshxona Bron Qilish Bot
**Texnologiyalar:** FastAPI + Telegram Bot + SQLite
**Port:** 8000 (API), Bot webhook/polling
**Database:** SQLite (production uchun PostgreSQL tavsiya etiladi)

## 🏗️ Arxitektura

```
bookingbot/
├── backend/              # Python backend + bot
│   ├── main.py          # FastAPI server
│   ├── bot.py           # Telegram bot
│   ├── database.py      # DB models
│   ├── requirements.txt # Dependencies
│   └── .env            # Environment variables
├── frontend/            # Static frontend files
├── docker-compose.yml   # Docker compose config
├── Dockerfile          # Docker image config
└── bookings.db         # SQLite database file
```

## 🔧 Server Talablari

### Minimum Requirements:
- **CPU:** 1 vCore
- **RAM:** 512MB
- **Storage:** 5GB
- **OS:** Ubuntu 20.04+ / CentOS 8+ / Debian 11+

### Recommended Requirements:
- **CPU:** 2 vCore
- **RAM:** 1GB
- **Storage:** 10GB
- **OS:** Ubuntu 22.04 LTS

## 📦 Kerakli Software

```bash
# Docker va Docker Compose o'rnatish
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo apt install docker-compose-plugin

# Git o'rnatish
sudo apt update
sudo apt install git

# Nginx o'rnatish (reverse proxy uchun)
sudo apt install nginx

# Certbot o'rnatish (SSL uchun)
sudo apt install certbot python3-certbot-nginx
```

## 🚀 Deploy Jarayoni

### 1. Repository Clone Qilish

```bash
# Server ga kirish va loyihani clone qilish
git clone <REPOSITORY_URL> /opt/bookingbot
cd /opt/bookingbot

# Fayllar huquqlarini sozlash
sudo chown -R $USER:$USER /opt/bookingbot
chmod +x run.py
```

### 2. Environment Variables Sozlash

```bash
# Backend .env fayli yaratish
cp backend/.env.example backend/.env
nano backend/.env
```

### 3. Docker Build va Run

```bash
# Docker containers ni build qilish va ishga tushirish
docker-compose up -d --build

# Containerlar holatini tekshirish
docker-compose ps
docker-compose logs -f
```

### 4. Nginx Reverse Proxy Sozlash

```bash
# Nginx config yaratish
sudo nano /etc/nginx/sites-available/bookingbot
```

Nginx config fayli:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /opt/bookingbot/frontend/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

```bash
# Nginx config ni faollashtirish
sudo ln -s /etc/nginx/sites-available/bookingbot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 5. SSL Sertifikat O'rnatish

```bash
# Let's Encrypt SSL sertifikat olish
sudo certbot --nginx -d your-domain.com

# Avtomatik yangilash uchun cron job qo'shish
sudo crontab -e
# Quyidagi qatorni qo'shing:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

### 6. Firewall Sozlash

```bash
# UFW firewall sozlash
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
```

## 🔐 Environment Variables

Backend `.env` faylida quyidagi o'zgaruvchilar bo'lishi kerak:

```env
# Telegram Bot Settings
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_CHAT_ID=admin_chat_id_here

# Database Settings
DATABASE_URL=sqlite:///./bookings.db

# Optional: Google Sheets Integration
GOOGLE_SHEET_ID=your_google_sheet_id

# Production Settings
ENVIRONMENT=production
DEBUG=false
```

## 🗄️ Database Migration

Agar SQLite dan PostgreSQL ga o'tish kerak bo'lsa:

```bash
# PostgreSQL o'rnatish
sudo apt install postgresql postgresql-contrib

# Database yaratish
sudo -u postgres createdb bookingbot
sudo -u postgres createuser bookingbot_user

# .env da DATABASE_URL yangilash
DATABASE_URL=postgresql://bookingbot_user:password@localhost/bookingbot
```

## 📊 Monitoring va Logging

### Logs ko'rish:
```bash
# Docker logs
docker-compose logs api
docker-compose logs bot

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Health Check:
```bash
# API health check
curl http://localhost:8000/

# Container holatini tekshirish
docker-compose ps
```

## 🔄 Update va Backup

### Loyihani yangilash:
```bash
cd /opt/bookingbot
git pull origin main
docker-compose down
docker-compose up -d --build
```

### Database backup:
```bash
# SQLite backup
cp bookings.db bookings_backup_$(date +%Y%m%d).db

# Backup scriptini yaratish
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cp /opt/bookingbot/bookings.db /opt/backups/bookings_$DATE.db
find /opt/backups -name "bookings_*.db" -mtime +7 -delete
EOF

chmod +x backup.sh

# Cron job qo'shish (har kuni soat 2:00 da)
# 0 2 * * * /opt/bookingbot/backup.sh
```

## 🛠️ Troubleshooting

### Umumiy muammolar:

1. **Bot ishlamayapti:**
   ```bash
   docker-compose logs bot
   # BOT_TOKEN ni tekshiring
   ```

2. **API 502 xatosi:**
   ```bash
   docker-compose ps
   # Container ishlab turganini tekshiring
   ```

3. **SSL muammolari:**
   ```bash
   sudo certbot certificates
   sudo nginx -t
   ```

4. **Database xatolari:**
   ```bash
   # Database faylining mavjudligini tekshiring
   ls -la bookings.db
   ```

## 📞 Qo'llab-quvvatlash

Muammolar yuzaga kelganda:

1. Logs ni tekshiring: `docker-compose logs`
2. Container holatini ko'ring: `docker-compose ps`
3. Disk joyini tekshiring: `df -h`
4. Memory ishlatilishini ko'ring: `free -m`

## 🔒 Xavfsizlik

### Production uchun xavfsizlik choralar:

1. **Firewall sozlash:** Faqat kerakli portlarni ochish
2. **SSH kalitlari:** Password autentifikatsiyani o'chirish
3. **Avtomatik backup:** Muntazam ma'lumotlar zaxirasi
4. **Log monitoring:** Xavfsizlik hodisalarini kuzatish
5. **SSL sertifikat:** HTTPS majburiy qilish

### SSH sozlash:
```bash
# SSH config yangilash
sudo nano /etc/ssh/sshd_config

# Quyidagi sozlamalarni o'zgartiring:
PasswordAuthentication no
PermitRootLogin no
Port 2222  # Standart portni o'zgartirish

sudo systemctl reload ssh
```

---

**Eslatma:** Bu yo'riqnoma production server uchun mo'ljallangan. Test muhit uchun ba'zi xavfsizlik choralari ixtiyoriy.