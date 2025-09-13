# Loyiha xotirasi va davom ettirish uchun ma'lumotlar

## Loyiha tavsifi
**Sartaroshxona bron qilish bot** - Telegram bot orqali sartaroshxonaga vaqt buyurtma qilish tizimi.

## Texnologiyalar
- **Backend**: Python, FastAPI, python-telegram-bot, SQLAlchemy, SQLite
- **Frontend**: HTML, Tailwind CSS, Vanilla JS, Telegram Web App API
- **Deploy**: Backend - local/server, Frontend - GitHub Pages/Vercel

## Loyiha strukturasi
```
bookingbot/
├── backend/          # Python backend
│   ├── venv/        # Virtual environment
│   ├── bot.py       # Telegram bot logikasi
│   ├── main.py      # FastAPI REST API
│   ├── database.py  # SQLAlchemy models
│   ├── run.py       # Ishga tushirish scripti
│   ├── requirements.txt
│   └── .env         # BOT_TOKEN, ADMIN_CHAT_ID
├── frontend/         # Web App
│   ├── index.html   # Calendar UI
│   ├── app.js       # JavaScript logika
│   └── vercel.json
└── README.md
```

## Asosiy funksiyalar (tugallangan)
✅ **User registration** - Telegram orqali ism va telefon qabul qilish  
✅ **Calendar interface** - Sana tanlash uchun calendar  
✅ **Time slots** - 09:00-22:00 oralig'ida soatlik slotlar  
✅ **Booking conflicts** - Bir vaqtga ikkita bron qilinmaydi  
✅ **Admin notifications** - Har yangi bron haqida admin ga xabar  
✅ **Database** - Users va Bookings jadvallar bilan SQLite  
✅ **Web App integration** - Telegram Web App orqali frontend  

## Hozirgi sozlamalar
- **Bot Token**: `8015680336:AAHWECAh0WpH90WB4FeSUbcJ-RqCYruyw3A`
- **Admin Chat ID**: `1483997295` 
- **Frontend URL**: `https://mirzobek-kxaitov.github.io/botfront/`
- **API URL**: `https://overluscious-unbusily-ralph.ngrok-free.app`
- **Server Port**: `8000`

## API Endpoints
- `GET /available-times/{date}` - Sana uchun bo'sh vaqtlar
- `GET /bookings/{date}` - Sana uchun mavjud bronlar

## Ishga tushirish buyruqlari
```bash
# Backend
cd backend
python run.py install  # Dependencies o'rnatish  
python run.py bot      # Bot ishga tushirish
python run.py api      # API server (port 8000)

# Frontend
# GitHub Pages yoki Vercel ga deploy qilingan
```

## Keyingi ishlar (opsional)
- [ ] Bron bekor qilish funksiyasi
- [ ] Admin panel (bronlarni ko'rish/boshqarish)
- [ ] SMS xabar yuborish
- [ ] Multiple xizmat turlari
- [ ] Haftalik/oylik hisobot
- [ ] Foydalanuvchi tarixi

## Xatolik yechish
- **CORS xatoligi**: `ngrok-skip-browser-warning` header qo'shildi
- **Network xatolik**: Batafsil error handling qo'shildi
- **Telegram Web App**: URL va integration sozlangan

## Muhim fayllar
- `bot.py:17` - WEBAPP_URL o'zgartiriladi
- `app.js:8` - API_BASE_URL o'zgartiriladi  
- `.env` - Bot token va admin ID
- `database.py` - DB schema
- `README.md` - To'liq yo'riqnoma

Bu ma'lumotlar bilan loyihani istalgan vaqtda davom ettirish mumkin.

## Oxirgi o'zgarishlar
- Frontend: GitHub Pages ga deploy qilindi
- API: ngrok orqali expose qilindi
- Error handling: API so'rovlarda yaxshilandi
- Telegram WebApp: To'liq integratsiya qilindi