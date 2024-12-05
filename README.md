# Do'stlik Testi Telegram Boti

## Qisqacha tavsif
Ushbu Telegram boti orqali siz do'stlaringiz bilan men do'stlik testini o'tkazishingiz mumkin. Bot sizga:
- Test yaratish
- Testni do'stlarga yuborish
- Do'stlarning javoblarini qayd etish
- Natijalarni ko'rish imkonini beradi

## O'rnatish
1. Python va pip o'rnatilganligiga ishonch hosil qiling
2. Kerakli kutubxonalarni o'rnatish:
```bash
pip install -r requirements.txt
```

3. `.env` faylga o'z Telegram bot tokeningizni kiriting

## Ishga tushirish
```bash
python main.py
```

## Foydalanish yo'riqnomasi
1. `/start` buyrug'i orqali botni ishga tushiring
2. `/create_test` orqali yangi test yarating
3. Chiqgan linkni do'stlaringizga yuboring
4. Do'stlaringiz testni bajarishadi
5. Natijalarni ko'ring

## Texnik ma'lumotlar
- Aiogram 3.1.1 asosida qurilgan
- Python 3.8+ talab etiladi
- Barcha ma'lumotlar vaqtincha xotirada saqlanadi

## Litsenziya
MIT Litsenziyasi
