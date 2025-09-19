# 🖥️ Server Setup - DevOps uchun Qadamlar

Bu hujjat serverga loyihani deploy qilish uchun DevOps mutaxassis uchun qadamli yo'riqnomadir.

## 📋 Boshlash Oldidan

**Domain:** Sizning domeningiz (masalan: `mybookingbot.com`)
**Server IP:** Sizning server IP manzilingiz
**SSH Access:** Root yoki sudo huquqlari bilan kirish

## 🏃‍♂️ Tezkor Deploy (Production Ready)

### 1. Server ga Kirish va Tayyorlash

```bash
# Server ga SSH orqali kirish
ssh root@YOUR_SERVER_IP

# Tizimni yangilash
apt update && apt upgrade -y

# Asosiy paketlarni o'rnatish
apt install -y curl wget git nano htop ufw

# Docker o'rnatish
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Docker Compose o'rnatish
apt install -y docker-compose-plugin

# Nginx o'rnatish
apt install -y nginx

# Certbot o'rnatish (SSL uchun)
apt install -y certbot python3-certbot-nginx
```

### 2. Loyihani Clone Qilish

```bash
# Loyiha papkasini yaratish
mkdir -p /opt/bookingbot
cd /opt/bookingbot

# Git repository clone qilish
git clone https://github.com/YOUR_USERNAME/bookingbot.git .

# Fayllar huquqlarini sozlash
chown -R www-data:www-data /opt/bookingbot
chmod +x run.py
```

### 3. Environment Variables Sozlash

```bash
# Backend .env faylini yaratish
cp backend/.env.example backend/.env

# .env faylini tahrirlash
nano backend/.env
```

**Quyidagi ma'lumotlarni to'ldiring:**
```env
BOT_TOKEN=1234567890:YOUR_ACTUAL_BOT_TOKEN
ADMIN_CHAT_ID=123456789
DATABASE_URL=sqlite:///./bookings.db
ENVIRONMENT=production
DEBUG=false
```

### 4. Docker Containers Ishga Tushirish

```bash
# Docker containers ni build va run qilish
docker-compose up -d --build

# Containerlar holatini tekshirish
docker-compose ps

# Loglarni ko'rish
docker-compose logs -f
```

### 5. Nginx Reverse Proxy Sozlash

```bash
# Nginx config faylini yaratish
nano /etc/nginx/sites-available/bookingbot
```

**Nginx konfiguratsiyasi:**
```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN.com www.YOUR_DOMAIN.com;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;

    # API proxy
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeout settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files
    location /static/ {
        alias /opt/bookingbot/frontend/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

```bash
# Nginx config ni faollashtirish
ln -s /etc/nginx/sites-available/bookingbot /etc/nginx/sites-enabled/

# Default config ni o'chirish
rm /etc/nginx/sites-enabled/default

# Nginx syntax ni tekshirish
nginx -t

# Nginx ni qayta yuklash
systemctl reload nginx
```

### 6. SSL Sertifikat O'rnatish

```bash
# Let's Encrypt SSL sertifikat olish
certbot --nginx -d YOUR_DOMAIN.com -d www.YOUR_DOMAIN.com

# SSL avtomatik yangilash uchun cron job
crontab -e
```

**Cron job qo'shish:**
```bash
# SSL sertifikatni har kuni tekshirish va yangilash
0 12 * * * /usr/bin/certbot renew --quiet --nginx
```

### 7. Firewall Sozlash

```bash
# UFW firewall yoqish
ufw --force enable

# SSH portini ochish
ufw allow ssh
ufw allow 22

# HTTP va HTTPS portlarini ochish
ufw allow 'Nginx Full'

# Firewall holatini ko'rish
ufw status
```

### 8. Systemd Service Yaratish (Ixtiyoriy)

```bash
# Systemd service faylini yaratish
nano /etc/systemd/system/bookingbot.service
```

**Service konfiguratsiyasi:**
```ini
[Unit]
Description=Booking Bot Service
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=true
WorkingDirectory=/opt/bookingbot
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

```bash
# Service ni faollashtirish
systemctl enable bookingbot.service
systemctl start bookingbot.service
```

## 🔧 Post-Deploy Tekshirish

### 1. Sog'lik Tekshirish

```bash
# API ni tekshirish
curl http://localhost:8000/
curl https://YOUR_DOMAIN.com/

# Bot loglarini ko'rish
docker-compose logs bot

# Nginx holatini tekshirish
systemctl status nginx
```

### 2. Monitoring Sozlash

```bash
# Log rotation sozlash
nano /etc/logrotate.d/bookingbot
```

**Log rotation konfiguratsiyasi:**
```
/opt/bookingbot/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
}
```

### 3. Backup Script Yaratish

```bash
# Backup papkasini yaratish
mkdir -p /opt/backups

# Backup scriptini yaratish
nano /opt/scripts/backup.sh
```

**Backup script:**
```bash
#!/bin/bash

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/opt/backups"
PROJECT_DIR="/opt/bookingbot"

# Database backup
cp "$PROJECT_DIR/bookings.db" "$BACKUP_DIR/bookings_$DATE.db"

# Environment backup
cp "$PROJECT_DIR/backend/.env" "$BACKUP_DIR/env_$DATE.backup"

# 7 kundan eski backuplarni o'chirish
find "$BACKUP_DIR" -name "bookings_*.db" -mtime +7 -delete
find "$BACKUP_DIR" -name "env_*.backup" -mtime +7 -delete

echo "Backup completed: $DATE"
```

```bash
# Script ni executable qilish
chmod +x /opt/scripts/backup.sh

# Har kuni soat 2:00 da backup olish uchun cron job
crontab -e
```

**Cron job:**
```bash
0 2 * * * /opt/scripts/backup.sh >> /var/log/backup.log 2>&1
```

## 🔄 Update Jarayoni

```bash
# Loyihani yangilash
cd /opt/bookingbot
git pull origin main

# Containers ni qayta build qilish
docker-compose down
docker-compose up -d --build

# Loglarni tekshirish
docker-compose logs -f
```

## 🚨 Troubleshooting

### Umumiy Muammolar:

1. **Docker ishlamayapti:**
   ```bash
   systemctl status docker
   systemctl start docker
   ```

2. **Bot webhook conflicts:**
   ```bash
   docker-compose logs bot
   # Loglardan "409 Conflict" xatosini izlang
   ```

3. **SSL sertifikat muammolari:**
   ```bash
   certbot certificates
   nginx -t
   ```

4. **Database ruxsat muammolari:**
   ```bash
   chown -R www-data:www-data /opt/bookingbot/
   chmod 664 /opt/bookingbot/bookings.db
   ```

### Log Fayllar Joylashuvi:

- **Nginx logs:** `/var/log/nginx/`
- **Docker logs:** `docker-compose logs`
- **System logs:** `/var/log/syslog`
- **SSL logs:** `/var/log/letsencrypt/`

## 📞 Qo'llab-quvvatlash Kontaktlari

**Developer:** [Sizning kontaktingiz]
**Loyiha Repository:** [GitHub link]
**Documentation:** `/opt/bookingbot/README.md`

---

## 🔐 Xavfsizlik Nasihatlar

1. **SSH kalitlardan foydalaning** (password auth ni o'chiring)
2. **Firewall ni to'g'ri sozlang** (faqat kerakli portlar)
3. **Muntazam backup oling**
4. **Loglarni kuzatib turing**
5. **SSL sertifikatni yangilab turing**

**Muvaffaqiyatli Deploy uchun omad tilaymiz! 🚀**