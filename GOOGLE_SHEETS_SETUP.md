# 📊 Google Sheets Integration - 5 Daqiqada Sozlash

Bu yo'riqnoma orqali siz botingizni Google Sheets bilan ulab, har bir bron avtomatik jadvalga kirib borishini ta'minlaysiz.

## 🎯 Natija

✅ Har yangi bron avtomatik Google Sheets ga yoziladi
✅ Mijoz ismi, telefoni, sana, vaqt - hammasi jadvalda
✅ Excel formatida yuklab olish mumkin
✅ Real-time yangilanish

---

## 📋 1-QADAM: Google Sheet Yaratish

### 1.1. Google Sheets ga kirish
```
🔗 https://sheets.google.com
```

### 1.2. Yangi jadval yaratish
- **"Blank"** tugmasini bosing
- Jadval nomi: **"Sartaroshxona Bronlar"**

### 1.3. Jadval linkini nusxalash
```
Masalan: https://docs.google.com/spreadsheets/d/1aWhfN0_AX1yT5yCRgdXZxTKjIiBoGVq4v2hdS29Bopk/edit

Sheet ID: 1aWhfN0_AX1yT5yCRgdXZxTKjIiBoGVq4v2hdS29Bopk
```

**💡 Sheet ID ni saqlab qoying!**

---

## 🔧 2-QADAM: Google Cloud Service Account

### 2.1. Google Cloud Console ga kirish
```
🔗 https://console.cloud.google.com
```

### 2.2. Yangi loyiha yaratish (agar yo'q bo'lsa)
- **"Select a project"** → **"New Project"**
- Loyiha nomi: **"Barbershop Bot"**
- **"Create"** tugmasini bosing

### 2.3. Google Sheets API ni yoqish
1. **"APIs & Services"** → **"Library"**
2. **"Google Sheets API"** ni qidiring
3. **"ENABLE"** tugmasini bosing

### 2.4. Google Drive API ni yoqish
1. **"Library"** da **"Google Drive API"** ni qidiring
2. **"ENABLE"** tugmasini bosing

---

## 🔑 3-QADAM: Service Account Yaratish

### 3.1. Credentials yaratish
1. **"APIs & Services"** → **"Credentials"**
2. **"+ CREATE CREDENTIALS"** → **"Service account"**

### 3.2. Service Account ma'lumotlari
```
Service account name: barbershop-bot
Service account ID: barbershop-bot (avtomatik)
Description: Bot for barbershop bookings
```
**"CREATE AND CONTINUE"** tugmasini bosing

### 3.3. Role berish
- **"Select a role"** → **"Editor"**
- **"CONTINUE"** → **"DONE"**

### 3.4. JSON kalitini yuklab olish
1. Yaratilgan **Service Account** ga kirish
2. **"Keys"** tab → **"ADD KEY"** → **"Create new key"**
3. **"JSON"** formatni tanlash
4. **"CREATE"** tugmasi → fayl yuklab olinadi

**📁 Yuklab olingan fayl nomi: `barbershop-bot-xxxxx.json`**

---

## 🔐 4-QADAM: Ruxsat Berish

### 4.1. Service Account email manzilini nusxalash
JSON faylini ochib, **"client_email"** ni topish:
```json
{
  "client_email": "barbershop-bot@your-project.iam.gserviceaccount.com"
}
```

### 4.2. Google Sheets ga ruxsat berish
1. Yaratgan **Google Sheets** ni ochish
2. **"Share"** tugmasini bosish
3. Service Account emailini qo'shish
4. **"Editor"** ruxsati berish
5. **"Send"** tugmasini bosish

---

## 💻 5-QADAM: Bot ga Fayl Qo'shish

### 5.1. JSON faylini nomini o'zgartirish
```bash
barbershop-bot-xxxxx.json → credentials.json
```

### 5.2. Faylni backend papkaga ko'chirish
```
bookingbot/
└── backend/
    ├── credentials.json  ← Bu yerga qo'ying
    ├── bot.py
    ├── .env
    └── ...
```

### 5.3. .env fayliga Sheet ID qo'shish
```env
BOT_TOKEN=8364626022:AAFdatmdnX3SiAAn5pANk3Ni3XoT1qeJ114
ADMIN_CHAT_ID=599321781
DATABASE_URL=sqlite:///./bookings.db
GOOGLE_SHEET_ID=1aWhfN0_AX1yT5yCRgdXZxTKjIiBoGVq4v2hdS29Bopk
ENVIRONMENT=production
DEBUG=false
```

---

## 📦 6-QADAM: Dependencies O'rnatish

### 6.1. Requirements.txt ni yangilash
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-telegram-bot==20.7
sqlalchemy==2.0.23
python-multipart==0.0.6
python-dotenv==1.0.0
pydantic==2.5.0
gspread==5.12.0
oauth2client==4.1.3
```

### 6.2. Dependencies o'rnatish
```bash
pip install gspread oauth2client
```

---

## ✅ 7-QADAM: Test Qilish

### 7.1. Botni ishga tushirish
```bash
cd backend
python bot.py
```

### 7.2. Test bron qilish
1. Telegram da botga **/start** yuboring
2. Bron qiling
3. Google Sheets ni tekshiring

### 7.3. Kutilgan natija
```
Google Sheets da jadval:
| ID | Mijoz Ismi | Telefon | Sana | Vaqt | Yaratilgan Vaqt | Status | Telegram ID |
|----|------------|---------|------|------|-----------------|--------|-------------|
| 1  | John Doe   | +998... | 2024-01-15 | 10:00 | 2024-01-15 09:30:00 | Aktiv | 123456789 |
```

---

## 🚨 Xatolarni Hal Qilish

### Xato: "credentials.json fayli topilmadi"
```bash
# Faylning joylashuvini tekshiring
ls -la backend/credentials.json

# Agar yo'q bo'lsa
cp ~/Downloads/barbershop-bot-xxxxx.json backend/credentials.json
```

### Xato: "GOOGLE_SHEET_ID topilmadi"
```bash
# .env faylini tekshiring
cat backend/.env | grep GOOGLE_SHEET_ID

# Agar yo'q bo'lsa, qo'shing
echo "GOOGLE_SHEET_ID=your_sheet_id_here" >> backend/.env
```

### Xato: "Permission denied"
```bash
# Google Sheets da ruxsat berilganini tekshiring
# Service Account emailiga "Editor" ruxsati kerak
```

### Xato: "Module 'gspread' not found"
```bash
# Dependencies o'rnatish
pip install gspread oauth2client
```

---

## 🎉 Tayyor!

Google Sheets integration muvaffaqiyatli sozlandi!

**Endi har yangi bron:**
✅ SQLite database ga saqlanadi
✅ Google Sheets ga avtomatik yoziladi
✅ Admin ga Telegram da xabar keladi

**Google Sheets imkoniyatlari:**
📊 Real-time jadval ko'rish
📥 Excel formatida export
📈 Statistika va hisobotlar
👥 Boshqa odamlar bilan ulashish

---

## 📞 Qo'llab-quvvatlash

Agar muammo bo'lsa:
1. **Loglarni tekshiring:** `docker-compose logs bot`
2. **Fayllar mavjudligini tasdiqlang:** `credentials.json` va `GOOGLE_SHEET_ID`
3. **Ruxsatlarni tekshiring:** Google Sheets da Service Account email
4. **Dependencies:** `gspread` va `oauth2client` o'rnatilgan

**Muvaffaqiyatli Google Sheets integratsiyasi uchun omad! 🚀**