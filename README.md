# Barbershop Booking Bot

Telegram bot va FastAPI backend orqali sartaroshxona bron qilish tizimi.

## Proyekt tuzilishi

```
backend/
├── bot.py              # Telegram bot
├── main.py            # FastAPI backend
├── database.py        # Ma'lumotlar bazasi modellari
├── run.py            # Lokal ishga tushirish skripti
├── requirements.txt   # Python paketlar ro'yxati
├── .env              # Muhit o'zgaruvchilari
├── Dockerfile        # Docker konteyner konfiguratsiyasi
├── docker-compose.yml # Docker Compose konfiguratsiyasi
└── bookings.db       # SQLite ma'lumotlar bazasi
```

## Talablar

- Python 3.12+
- Docker va Docker Compose (ixtiyoriy)

## Sozlash

### 1. Muhit o'zgaruvchilarini sozlash

`.env` faylini yarating va quyidagi qiymatlarni kiriting:

```env
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_CHAT_ID=your_admin_chat_id_here
DATABASE_URL=sqlite:///./bookings.db
```

### 2. Telegram Bot tokenini olish

1. [@BotFather](https://t.me/BotFather) ga boring
2. `/newbot` buyrug'ini yuboring
3. Bot nomini va username ni kiriting
4. Olingan tokenni `.env` fayliga `BOT_TOKEN` sifatida qo'shing

## Lokal ishga tushirish

### Virtual environment bilan

```bash
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

### Faqat Docker

```bash
# Image yaratish
docker build -t bookingbot .

# API serverni ishga tushirish
docker run -d -p 8000:8000 \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/bookings.db:/app/bookings.db \
  --name bookingbot-api \
  bookingbot

# Botni ishga tushirish
docker run -d \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/bookings.db:/app/bookings.db \
  --name bookingbot-bot \
  bookingbot python bot.py
```

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

- **Backend**: FastAPI
- **Bot**: python-telegram-bot
- **Ma'lumotlar bazasi**: SQLite + SQLAlchemy
- **Server**: Uvicorn
- **Konteynerizatsiya**: Docker + Docker Compose

## Muammolarni hal qilish

### Bot ishlamayapti
1. `.env` faylidagi `BOT_TOKEN` to'g'riligini tekshiring
2. Bot tokenining faol ekanligini tekshiring

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