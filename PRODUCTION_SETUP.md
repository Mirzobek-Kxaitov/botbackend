# 🔧 Production Setup - Bot Token va Admin ID Sozlash

Bu hujjat sizning shaxsiy bot va admin ma'lumotlaringizni production serverga sozlash uchun.

## 📋 Kerakli Ma'lumotlar

Serverga deploy qilishdan oldin quyidagi ma'lumotlarni tayyorlang:

### 1. **Telegram Bot Token**
```bash
# @BotFather ga boring va yangi bot yarating
/newbot
# Bot nomini kiriting: "Sartaroshxona Booking Bot"
# Username kiriting: "your_barbershop_booking_bot"
# Token oling: 1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ
```

### 2. **Admin Chat ID**
```bash
# Bot yaratilgandan keyin:
# 1. Botga /start yuboring
# 2. Bot loglaridan yoki IDBot (@userinfobot) dan ID ni oling
# Misol: 123456789
```

## 🔧 Server da Sozlash

### 1. Environment Variables O'zgartirish

```bash
# Server da loyihani clone qilgandan keyin
cd /opt/bookingbot
nano backend/.env
```

### 2. .env Faylini To'ldirish

```env
# =================================
# PRODUCTION SOZLAMALARI
# =================================

# Sizning yangi bot tokeningiz
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ

# Sizning admin chat ID ingiz
ADMIN_CHAT_ID=123456789

# Database (SQLite yoki PostgreSQL)
DATABASE_URL=sqlite:///./bookings.db

# Muhit turi
ENVIRONMENT=production
DEBUG=false

# =================================
# IXTIYORIY SOZLAMALAR
# =================================

# Google Sheets integration (IXTIYORIY - agar avtomatik Excel jadval kerak bo'lsa)
GOOGLE_SHEET_ID=your_google_sheet_id_here

# Google Sheets dependencies (agar GOOGLE_SHEET_ID ishlatilsa)
# pip install gspread oauth2client
# credentials.json faylini backend/ papkaga qo'ying

# Frontend URL (agar alohida domain bo'lsa)
FRONTEND_URL=https://your-frontend-domain.com

# API Base URL
API_BASE_URL=https://your-api-domain.com
```

### 3. Xavfsizlik Tekshirish

```bash
# .env faylining huquqlarini cheklash
chmod 600 backend/.env

# Faqat owner o'qiy va yoza oladi
ls -la backend/.env
# Natija: -rw------- 1 user user 245 date backend/.env
```

## 🚀 Deploy Qilish

### 1. Docker bilan
```bash
# Containers ni build va run qilish
docker-compose up -d --build

# Loglarni tekshirish
docker-compose logs bot
docker-compose logs api
```

### 2. Manual bilan
```bash
# Virtual environment yaratish
cd backend
python3 -m venv venv
source venv/bin/activate

# Dependencies o'rnatish
pip install -r requirements.txt

# Bot va API ni alohida terminallarda ishga tushirish
python bot.py &
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

## ✅ Test Qilish

### 1. Bot Test
```bash
# Telegram da botingizga:
/start
# Javob kelishi kerak: "Sartaroshxonaga xush kelibsiz!"
```

### 2. API Test
```bash
# Server da:
curl http://localhost:8000/
# Yoki browserda:
# https://your-domain.com/
```

### 3. Admin Notification Test
```bash
# Kimdir bot orqali bron qilganda
# Admin ga xabar kelishi kerak
```

## 🔒 Xavfsizlik Eslatmalar

### 1. **Token xavfsizligi**
- ❌ Hech qachon bot tokenni ochiq joyda qoldirmang
- ✅ Faqat server da `.env` faylida saqlang
- ✅ `.env` faylini git ga commit qilmang

### 2. **Access Control**
- ✅ Server ga faqat SSH kalitlari bilan kirish
- ✅ Firewall sozlangan bo'lishi
- ✅ Nginx reverse proxy ishlatish

### 3. **Monitoring**
- ✅ Bot loglarini kuzatib turing
- ✅ Error notifications sozlang
- ✅ Regular backup oling

## 🛠️ Troubleshooting

### Muammo: Bot javob bermayapti
```bash
# Bot loglarini tekshiring
docker-compose logs bot

# Yoki manual ishlatgan bo'lsangiz
tail -f bot.log
```

### Muammo: 409 Conflict error
```bash
# Boshqa bot instance ishlab turibdi
# Barcha bot processlarini to'xtating
pkill -f "python.*bot"

# Keyin qayta ishga tushiring
```

### Muammo: Database errors
```bash
# Database faylining mavjudligini tekshiring
ls -la bookings.db

# Huquqlarni tekshiring
chmod 664 bookings.db
```

## 📞 Qo'llab-quvvatlash

Agar deploy paytida muammolar bo'lsa:

1. **Loglarni tekshiring** - har doim birinchi qadam
2. **Environment variables** - to'g'ri to'ldirilganini tasdiqlang
3. **Network/Firewall** - portlar ochiqligini tekshiring
4. **Dependencies** - barcha paketlar o'rnatilganini tekshiring

---

**Muvaffaqiyatli deploy uchun omad tilaymiz! 🎉**