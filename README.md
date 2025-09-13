# Sartaroshxona Bron Qilish Bot 💇‍♂️

Telegram bot orqali sartaroshxonaga bron qilish tizimi.

## Loyiha strukturasi

```
bookingbot/
├── backend/          # Python backend (FastAPI + Telegram bot)
│   ├── venv/        # Virtual environment
│   ├── bot.py       # Telegram bot
│   ├── main.py      # FastAPI server
│   ├── database.py  # Database models
│   ├── run.py       # Ishga tushirish scripti
│   ├── requirements.txt
│   └── .env.example
├── frontend/         # HTML/CSS/JS frontend (Vercel uchun)
│   ├── index.html
│   ├── app.js
│   └── vercel.json
└── README.md
```

## Sozlash

### 1. Backend sozlash

```bash
cd backend

# Virtual environment yaratish
python3 -m venv venv

# Virtual environment faolllashtirish
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate

# Dependencies o'rnatish
pip install -r requirements.txt

# Environment variables sozlash
cp .env .env
# .env fayliga bot token va admin chat ID ni yozing
```

### 2. .env fayl sozlash

```env
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_CHAT_ID=your_admin_chat_id_here
DATABASE_URL=sqlite:///./bookings.db
```

### 3. Bot ishga tushirish

```bash
# Requirements o'rnatish
python run.py install

# Bot ishga tushirish
python run.py bot

# Yoki FastAPI server (alohida terminallda)
python run.py api
```

### 4. Frontend deploy (Vercel)

1. Frontend papkasini Vercel ga deploy qiling
2. `frontend/app.js` fayldagi `API_BASE_URL` ni o'zgartiring
3. `backend/bot.py` fayldagi `WEBAPP_URL` ni yangilang

## Bot funksiyalari

### Foydalanuvchilar uchun:
- `/start` - Bot bilan tanishish va ro'yxatdan o'tish
- Ism va telefon raqam berish
- Calendar orqali sana tanlash
- Mavjud vaqtlar orasidan tanlash
- Bron tasdiqlash

### Admin uchun:
- Har yangi bron haqida xabar olish
- Mijoz ma'lumotlari (ism, telefon, sana, vaqt)

### Texnik xususiyatlar:
- **Vaqt oralig'i**: 09:00 - 22:00 (har soat)
- **Konflikt oldini olish**: Bir vaqtga faqat bitta bron
- **Ma'lumotlar bazasi**: SQLite
- **Web App**: Telegram Web App orqali frontend

## Dasturlash tillari va texnologiyalar

### Backend:
- **Python 3.9+**
- **FastAPI** - REST API
- **python-telegram-bot** - Telegram bot API
- **SQLAlchemy** - Database ORM
- **SQLite** - Database

### Frontend:
- **HTML5**
- **Tailwind CSS**
- **Vanilla JavaScript**
- **Telegram Web Apps API**

## API Endpoints

- `GET /` - API holati
- `GET /available-times/{date}` - Sana uchun mavjud vaqtlar
- `GET /bookings/{date}` - Sana uchun mavjud bronlar

## Foydalanish uchun qadamlar

1. BotFather orqali yangi bot yarating
2. Admin chat ID ni aniqlang
3. Backend sozlab ishga tushiring  
4. Frontend ni Vercel ga deploy qiling
5. Bot da Web App URL ni yangilang
6. Botni Telegram da ishlatishni boshlang

## Xavfsizlik

- Bot faqat ro'yxatdan o'tgan foydalanuvchilar bilan ishlaydi
- Har bir foydalanuvchi faqat o'z akkauntiga bron qila oladi
- Admin faqat bildirishnoma oladi, bron o'zgartira olmaydi

## Muammolarni hal qilish

### Bot ishlamayapti:
1. BOT_TOKEN to'g'ri ekanligini tekshiring
2. Bot faol ekanligini tekshiring (/start buyrug'i bilan)
3. Network ulanishini tekshiring

### Frontend ishlamayapti:
1. API_BASE_URL to'g'ri URL ekanligini tekshiring
2. CORS sozlamalarini tekshiring
3. Browser console da xatolarni ko'ring

### Database xatoliklari:
1. SQLite fayli mavjudligini tekshiring
2. Database permission larni tekshiring
3. Virtual environment faol ekanligini tekshiring