# Sartaroshxona Bron Qilish Bot 💇‍♂️

Telegram bot va FastAPI backend orqali sartaroshxona bron qilish tizimi.

## Proyekt tuzilishi

```
bookingbot/
├── backend/          # Python backend (FastAPI + Telegram bot)
│   ├── venv/        # Virtual environment
│   ├── bot.py       # Telegram bot
│   ├── main.py      # FastAPI backend
│   ├── database.py  # Ma'lumotlar bazasi modellari
│   ├── run.py       # Lokal ishga tushirish skripti
│   ├── requirements.txt   # Python paketlar ro'yxati
│   ├── .env         # Muhit o'zgaruvchilari
│   ├── Dockerfile   # Docker konteyner konfiguratsiyasi
│   ├── docker-compose.yml # Docker Compose konfiguratsiyasi
│   └── bookings.db  # SQLite ma'lumotlar bazasi
├── frontend/         # HTML/CSS/JS frontend (Vercel uchun)
│   ├── index.html
│   ├── app.js
│   └── vercel.json
└── README.md
```

## Talablar

- Python 3.12+
- Docker va Docker Compose (ixtiyoriy)

## Sozlash

### 1. Muhit o'zgaruvchilarini sozlash

`backend/.env` faylini yarating yoki `.env.example` dan nusxalab, quyidagi qiymatlarni to'ldiring:

```env
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_CHAT_ID=your_admin_chat_id_here
DATABASE_URL=sqlite:///./bookings.db
ENVIRONMENT=production
DEBUG=false
```

**⚠️ Muhim:** Production da o'z bot tokeningizni va admin ID ngizni ishlating!

### 2. Telegram Bot tokenini olish

1. [@BotFather](https://t.me/BotFather) ga boring
2. `/newbot` buyrug'ini yuboring
3. Bot nomini va username ni kiriting
4. Olingan tokenni `.env` fayliga `BOT_TOKEN` sifatida qo'shing

## Lokal ishga tushirish

### Virtual environment bilan

```bash
cd backend

# Virtual environment yaratish
python3 -m venv venv

# Faollashtirish (Linux/Mac)
source venv/bin/activate

# Faollashtirish (Windows)
venv\Scripts\activate

# Paketlarni o'rnatish
pip install -r requirements.txt

# Botni ishga tushirish
python run.py bot

# API serverni ishga tushirish (boshqa terminalda)
python run.py api
```

### run.py skripti bilan

```bash
# Paketlarni o'rnatish
python run.py install

# Botni ishga tushirish
python run.py bot

# API serverni ishga tushirish
python run.py api
```

## Docker bilan ishga tushirish

### Docker Compose (tavsiya etiladi)

```bash
# Barcha servislarni ishga tushirish
docker-compose up -d

# Loglarni ko'rish
docker-compose logs -f

# To'xtatish
docker-compose down
```

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

## API Endpoints

### GET `/`
Asosiy sahifa

### GET `/available-times/{date}`
Berilgan sanada bo'sh vaqtlarni olish

**Parametrlar:**
- `date`: Sana (YYYY-MM-DD formatida)

**Javob:**
```json
{
  "available_times": ["09:00", "10:00", "11:00", ...]
}
```

### GET `/bookings/{date}`
Berilgan sanadagi bronlarni olish

**Parametrlar:**
- `date`: Sana (YYYY-MM-DD formatida)

**Javob:**
```json
[
  {
    "id": 1,
    "date": "2024-01-15",
    "time": "10:00",
    "user_name": "John Doe",
    "user_phone": "+998901234567"
  }
]
```

## Bot buyruqlari

- `/start` - Botni ishga tushirish
- `/book` - Bron qilish
- `/my_bookings` - Mening bronlarim
- `/cancel` - Bronni bekor qilish
- `/help` - Yordam

## Texnologiyalar

- **Backend**: FastAPI + Python 3.9+
- **Bot**: python-telegram-bot
- **Ma'lumotlar bazasi**: SQLite + SQLAlchemy
- **Frontend**: HTML5, Tailwind CSS, Vanilla JavaScript
- **Server**: Uvicorn
- **Konteynerizatsiya**: Docker + Docker Compose

## Foydalanish uchun qadamlar

1. BotFather orqali yangi bot yarating
2. Admin chat ID ni aniqlang
3. Backend sozlab ishga tushiring
4. Frontend ni Vercel ga deploy qiling
5. Bot da Web App URL ni yangilang
6. Botni Telegram da ishlatishni boshlang

## Muammolarni hal qilish

### Bot ishlamayapti
1. `.env` faylidagi `BOT_TOKEN` to'g'riligini tekshiring
2. Bot tokenining faol ekanligini tekshiring

### Frontend ishlamayapti
1. API_BASE_URL to'g'ri URL ekanligini tekshiring
2. CORS sozlamalarini tekshiring
3. Browser console da xatolarni ko'ring

### Ma'lumotlar bazasi xatolari
1. `bookings.db` faylining mavjudligini tekshiring
2. Fayl ruxsatlarini tekshiring

### Port band
Agar 8000 port band bo'lsa, boshqa portni ishlating:
```bash
# Docker Compose
docker-compose up -d --build

# Lokal
python -m uvicorn main:app --host 0.0.0.0 --port 8001
```

## Ishlab chiqish

Ishlab chiqish muhitida qo'shimcha sozlamalar:

```bash
# Reload bilan ishga tushirish
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Debug rejimida bot
python bot.py
```
