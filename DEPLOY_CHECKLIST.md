# ✅ Deploy Checklist - DevOps uchun

## 📋 Pre-Deploy Tekshirish

- [ ] Server tayyorligi (RAM, CPU, Disk)
- [ ] Domain sozlamalari (DNS records)
- [ ] SSL sertifikat imkoniyati
- [ ] Bot token va admin chat ID mavjudligi

## 🔧 Server Sozlash

- [ ] Ubuntu/Debian server yangilangan
- [ ] Docker o'rnatilgan va ishlamoqda
- [ ] Docker Compose o'rnatilgan
- [ ] Nginx o'rnatilgan
- [ ] Git o'rnatilgan
- [ ] Firewall (UFW) sozlangan

## 📦 Loyiha Deploy

- [ ] Repository clone qilingan `/opt/bookingbot` ga
- [ ] `.env` fayli to'g'ri sozlangan
- [ ] Docker containers build qilingan
- [ ] API container ishlamoqda (port 8000)
- [ ] Bot container ishlamoqda
- [ ] Database fayli yaratilgan

## 🌐 Web Server Sozlash

- [ ] Nginx reverse proxy sozlangan
- [ ] Domain API ga yo'naltirilgan
- [ ] Static fayllar xizmat qilmoqda
- [ ] SSL sertifikat o'rnatilgan
- [ ] HTTPS redirect ishlamoqda

## 🔐 Xavfsizlik

- [ ] Firewall yoqilgan (faqat 22, 80, 443 portlar)
- [ ] SSH kalitlari sozlangan
- [ ] Password authentication o'chirilgan
- [ ] Bot token xavfsiz saqlangan

## 📊 Monitoring

- [ ] Nginx access/error logs tekshirilgan
- [ ] Docker containers loglar ko'rilgan
- [ ] API health check ishlamoqda
- [ ] Bot Telegram ga ulanib turibdi

## 🔄 Automation

- [ ] SSL avtomatik yangilanish (certbot cron)
- [ ] Database backup script sozlangan
- [ ] Log rotation sozlangan
- [ ] Systemd service (ixtiyoriy)

## ✅ Final Test

- [ ] Bot `/start` buyrug'iga javob bermoqda
- [ ] API `https://domain.com/` ishlayapti
- [ ] Bron qilish jarayoni to'liq ishlayapti
- [ ] Admin ga xabarlar kelmoqda
- [ ] Frontend sahifalari ochilmoqda

## 📞 Go-Live Checklist

- [ ] Production environment variables tekshirilgan
- [ ] Database backuplar ishlayapti
- [ ] Monitoring dashboard sozlangan
- [ ] Error notification larni sozlangan
- [ ] Developer ga test holatini bildirish
- [ ] User manualini admin ga uzatish

---

**Barcha checklistlar ✅ bo'lgach loyiha production ga tayyor!**