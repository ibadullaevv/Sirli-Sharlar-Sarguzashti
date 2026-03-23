# Sirli Sharlar Sarguzashti — Telegram Bot Qo'llanma

## 1. Botni sozlash

### 1.1 BotFather'dan token olish
1. Telegram'da [@BotFather](https://t.me/BotFather) ga yozing
2. `/newbot` buyrug'ini yuboring
3. Bot nomini kiriting: `Sirli Sharlar Bot`
4. Username kiriting: `sirli_sharlar_bot` (o'zingizga mos)
5. BotFather sizga **token** beradi — uni nusxalang

### 1.2 O'z Telegram ID'ingizni bilish
1. [@userinfobot](https://t.me/userinfobot) ga `/start` yuboring
2. U sizga ID raqamingizni ko'rsatadi (masalan: `123456789`)
3. Bir nechta admin bo'lsa — har birining ID'sini oling

### 1.3 `.env` faylni yaratish
Loyiha papkasida `.env` fayl yarating:
```
BOT_TOKEN=7123456789:AAH1234567890abcdefghijklmnop
ADMIN_IDS=123456789,987654321
```
- `BOT_TOKEN` — BotFather'dan olingan token
- `ADMIN_IDS` — admin ID'lar, vergul bilan ajratiladi

### 1.4 Botni ishga tushirish
```bash
cd marbleverse_quest
source venv/Scripts/activate
python bot.py
```
Konsolda `Bot ishga tushdi!` yozuvi chiqsa — tayyor.

---

## 2. O'yindan oldingi tayyorgarlik (1 kun avval)

### 2.1 Marbleverse'da marble'larni joylashtirish
| Bosqich | Lokatsiya | Maxfiy kod |
|---------|-----------|------------|
| 1 | Axborot markazi oldi | `BILIM2024` |
| 2 | Tarixiy xiyobon | `TABIAT2024` |
| 3 | Asosiy bino kirish qismi | `ILMDARVO` |
| 4 | Sport maydoni | `SPORT2024` |
| 5 | Oshxona atrofi | `FINAL2024` |

Har bir marble ichiga shu bosqichning maxfiy kodini yozing.

### 2.2 Botni test qilish
1. O'zingiz bilan test qiling — `/start` → ro'yxatdan o'ting
2. `/startgame` bering — topshiriq kelishini tekshiring
3. `/submit` → selfi → video → kod yuboring
4. Admin sifatida ✅ tasdiqlang — keyingi bosqich kelishini tekshiring
5. Hammasi ishlasa — DB'ni tozalang: `quest.db` faylni o'chiring

---

## 3. O'yin kuni — qadam-baqadam

### 3.1 Yig'ilish (boshlashdan 30 daqiqa oldin)

```
Admin qilishi:                         Jamoalar qilishi:
┌─────────────────────────┐            ┌─────────────────────────┐
│ 1. Botni ishga tushirish│            │ 1. Telefoniga Marbleverse│
│ 2. Jamoalarga bot       │            │    va Telegram o'rnatish │
│    linkini tarqatish    │            │ 2. Botga /start bosish   │
│ 3. Qoidalarni tushuntir │            │ 3. Jamoa nomi kiritish   │
│                         │            │ 4. A'zolar ismini kiritish│
└─────────────────────────┘            └─────────────────────────┘
```

### 3.2 Ro'yxatdan o'tish jarayoni (jamoa tomoni)

```
Jamoa: /start
  │
  ▼
Bot: "Jamoangiz nomini kiriting"
  │
  ▼
Jamoa: "Sheryuraklar"
  │
  ▼
Bot: "A'zolari ismlarini kiriting (vergul bilan)"
  │
  ▼
Jamoa: "Ali, Vali, Sardor, Nodira"
  │
  ▼
Bot: "✅ Sheryuraklar ro'yxatdan o'tdi!
      Marshrut: 1 → 2 → 3 → 4 → 5
      O'yin boshlanishini kuting..."
  │
  ▼
Admin'ga: "🆕 Yangi jamoa: Sheryuraklar"
```

### 3.3 O'yinni boshlash (admin)

Admin botga `/startgame` yozadi:
```
Admin: /startgame
  │
  ▼
Bot (admin'ga): "🚀 O'yin boshlandi! Jamoalar: 8 ta"
  │
  ▼
Bot (har jamoaga): "🚀 O'YIN BOSHLANDI!
                    Vaqt: 60 daqiqa
                    Marshrut: 2 → 3 → 4 → 5 → 1

                    📍 2-BOSQICH: TARIXIY XIYOBON
                    Topshiriqlar:
                    1️⃣ Sakrash selfisi...
                    2️⃣ 10 ta fakt..."
```

### 3.4 Topshiriq yuborish jarayoni (jamoa)

```
Jamoa: /submit
  │
  ▼
Bot: "📸 Selfi/rasm yuboring"
  │
  ├── Jamoa rasm yuboradi ──→ Bot: "📸 Qabul qilindi! 🎥 Video yuboring"
  │                               │
  │                               ├── Jamoa video yuboradi ──→ Bot: "🔑 Maxfiy kodni yozing"
  │                               │                                │
  │                               │                                ▼
  │                               │                           Jamoa: "TABIAT2024"
  │                               │                                │
  │                               │                           ┌────┴────┐
  │                               │                      Kod TO'G'RI   Kod NOTO'G'RI
  │                               │                           │              │
  │                               │                           ▼              ▼
  │                               │                    Bot: "✅ Yuborildi!   Bot: "❌ Kod noto'g'ri!
  │                               │                     Admin tekshirmoqda"  Qaytadan yozing"
  │                               │
  │                               └── /skip_video ──→ Bot: "🔑 Maxfiy kodni yozing"
  │
  └── /skip_photo ──→ Bot: "🎥 Video yuboring"
```

### 3.5 Admin tekshiruvi

```
Bot admin'ga yuboradi:
┌──────────────────────────────────┐
│ 📥 YANGI TOPSHIRIQ               │
│                                  │
│ Jamoa: Sheryuraklar (#3)         │
│ Bosqich: 2 — Tarixiy xiyobon    │
│ Kod: TABIAT2024 ✅               │
│                                  │
│ [✅ Tasdiqlash] [❌ Rad etish]    │
└──────────────────────────────────┘
+ 📸 selfi rasm
+ 🎥 video

Admin ✅ Tasdiqlash bossa:
  │
  ├──→ Jamoaga: "✅ 2-BOSQICH TASDIQLANDI!
  │              +3 ball — Jami: 5/12
  │              Keyingi bosqich yuklanmoqda..."
  │
  └──→ Bot keyingi bosqich topshirig'ini yuboradi

Admin ❌ Rad etish bossa:
  │
  ▼
Bot: "Rad etish sababini yozing"
  │
  ▼
Admin: "Selfida 2 ta a'zo ko'rinmayapti"
  │
  ▼
Jamoaga: "❌ TOPSHIRIQ RAD ETILDI
          Sabab: Selfida 2 ta a'zo ko'rinmayapti
          Qaytadan /submit bilan yuboring!"
```

### 3.6 Jamoa barcha bosqichlarni tugatganda

```
Bot jamoaga:
┌──────────────────────────────────┐
│ 🎉🎉🎉 TABRIKLAYMIZ! 🎉🎉🎉      │
│                                  │
│ Barcha bosqichlar tugatildi!     │
│ Yakuniy ball: 10/12              │
│ Umumiy vaqt: 00:47:23            │
│                                  │
│ Natijalar e'lon qilinishini      │
│ kuting!                          │
└──────────────────────────────────┘

Bot admin'ga:
"🏁 Sheryuraklar barcha bosqichlarni tugatdi!
 Ball: 10/12 | Vaqt: 00:47:23"
```

---

## 4. O'yin davomida admin buyruqlari

| Buyruq | Vazifasi | Misol |
|--------|----------|-------|
| `/startgame` | O'yinni boshlash | `/startgame` |
| `/endgame` | O'yinni yakunlash, natijalarni e'lon qilish | `/endgame` |
| `/pending` | Kutayotgan topshiriqlarni ko'rish | `/pending` |
| `/standings` | To'liq natijalar (ball, vaqt, a'zolar) | `/standings` |
| `/broadcast` | Barcha jamoalarga xabar yuborish | `/broadcast 10 daqiqa qoldi!` |
| `/leaderboard` | Natijalar jadvali | `/leaderboard` |

---

## 5. O'yinni yakunlash

### 5.1 Vaqt tugaganda
```
Admin: /broadcast Vaqt tugadi! Barcha jamoalar to'xtang!
Admin: /endgame
  │
  ▼
Bot barcha jamoalarga:
┌──────────────────────────────────┐
│ 🏁 O'YIN YAKUNLANDI!            │
│                                  │
│ 🏆 NATIJALAR JADVALI             │
│                                  │
│ 🥇 Sheryuraklar — 12 ball ✅     │
│    00:43:15                      │
│ 🥈 Qorsonlar — 10 ball ✅        │
│    00:51:02                      │
│ 🥉 Yulduzlar — 10 ball 📍4/5    │
│    —                             │
│ 4. Botirlar — 7 ball 📍3/5      │
│                                  │
│ 🏆 G'olib: Sheryuraklar — 12!   │
└──────────────────────────────────┘
```

### 5.2 G'olib aniqlash tartibi
1. **Eng ko'p ball** to'plagan jamoa (max 12)
2. Ball teng bo'lsa → **eng tez tugatgan** jamoa
3. Yana teng bo'lsa → admin qo'shimcha savol beradi

---

## 6. Jamoa uchun buyruqlar

| Buyruq | Vazifasi |
|--------|----------|
| `/start` | Ro'yxatdan o'tish |
| `/submit` | Topshiriq yuborish (selfi → video → kod) |
| `/myscore` | Joriy ball va bosqichni ko'rish |
| `/leaderboard` | Barcha jamoalar reytingi |
| `/time` | O'tgan va qolgan vaqtni ko'rish |
| `/help` | Yordam |

---

## 7. Muammolar va yechimlar

| Muammo | Yechim |
|--------|--------|
| Bot javob bermayapti | `python bot.py` ishlab turganini tekshiring |
| Jamoa ro'yxatdan o'ta olmayapti | Bot guruh chatda emas, shaxsiy chatda ishlaydi |
| Maxfiy kod qabul qilinmayapti | Katta-kichik harf farqi: `bilim2024` emas → `BILIM2024` |
| Selfi/video kelmayapti admin'ga | `ADMIN_IDS` to'g'ri yozilganini tekshiring |
| Internet yo'q joyda | Nazoratchi og'zaki kod beradi, selfi keyinroq yuboriladi |
| Marble topilmayapti | GPS yoqilganini, Marbleverse'da AR rejim ochilganini tekshiring |
| Jamoa noto'g'ri bosqichga bormoqda | Bot avtomatik to'g'ri tartibda yuboradi — faqat botdagi manzilga boring |

---

## 8. Fayl tuzilishi

```
marbleverse_quest/
├── .env              ← Token va admin ID'lar (MAXFIY — git'ga qo'shmang!)
├── .env.example      ← .env namunasi
├── .gitignore
├── requirements.txt  ← kutubxonalar ro'yxati
├── config.py         ← bosqichlar, marshrut, vaqt sozlamalari
├── database.py       ← SQLite baza (jamoalar, topshiriqlar)
├── bot.py            ← asosiy bot fayli
├── quest.db          ← ma'lumotlar bazasi (avtomatik yaratiladi)
├── senariy.txt       ← to'liq o'yin hujjati
└── BOT_QOLLANMA.md   ← shu fayl
```
