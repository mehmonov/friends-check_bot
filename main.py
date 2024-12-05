from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile,
    ReplyKeyboardMarkup,
    KeyboardButton
)
import logging
import os
import random
import tempfile
from database import Database
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)

# .env faylidan BOT_TOKEN ni o'qish
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi. .env faylini tekshiring.")

# Bot va dispatcher yaratish
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Database yaratish
db = Database()

# Test savollari
FRIENDSHIP_TEST_QUESTIONS = [
    {
        "question": "🎨 Men qanday rangni yaxshi ko'raman?",
        "options": ["❤️ Qizil", "💙 Ko'k", "💚 Yashil", "🤍 Oq"]
    },
    {
        "question": "🌺 Mening sevimli faslim qaysi?",
        "options": ["🌸 Bahor", "☀️ Yoz", "🍁 Kuz", "❄️ Qish"]
    },
    {
        "question": "⏰ Bo'sh vaqtimda nima qilishni yoqtiraman?",
        "options": ["📚 Kitob o'qish", "🏃 Sport bilan shug'ullanish", "👥 Do'stlar bilan uchrashish", "🏠 Uyda dam olish"]
    },
    {
        "question": "🎬 Qanday turdagi filmlarni ko'rishni yaxshi ko'raman?",
        "options": ["😂 Komediya", "🎭 Drama", "🚀 Fantastika", "🔍 Detektiv"]
    },
    {
        "question": "🍽️ Mening sevimli taomim nima?",
        "options": ["🍚 Osh", "🥟 Manti", "🍜 Lag'mon", "🍖 Shashlik"]
    }
]

# FSM holatlari
class TestStates(StatesGroup):
    waiting_for_answer = State()
    waiting_for_name = State()
    finished = State()

def get_inline_keyboard(options, prefix="answer"):
    """Inline klaviatura yaratish"""
    keyboard = []
    for i, option in enumerate(options):
        keyboard.append([InlineKeyboardButton(
            text=option,
            callback_data=f"{prefix}:{i}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@dp.message(Command(commands=["start"]))
async def cmd_start(message: types.Message, state: FSMContext):
    if message.text.startswith("/start test_"):
        test_id = message.text.split()[1]
        test_data = db.get_test(test_id)
        
        if not test_data:
            await message.answer(" Kechirasiz, bu test topilmadi yoki yaroqsiz!")
            return
        
        # Tekshirish: foydalanuvchi avval bu testni yechganmi
        if db.has_participant_completed(test_id, message.from_user.id):
            await message.answer(" Siz bu testni allaqachon yechib bo'lgansiz!")
            return
        
        await state.update_data(test_id=test_id, current_question=0, answers={})
        await state.set_state(TestStates.waiting_for_answer)
        
        # Birinchi savolni yuborish
        question = FRIENDSHIP_TEST_QUESTIONS[0]
        keyboard = get_inline_keyboard(question['options'], "friend_answer")
        
        await message.answer(
            " Salom! Sizning do'stingiz test yaratdi.\n"
            "Iltimos, savollarga javob bering va ko'ramiz qanchalik yaxshi bilasiz!\n\n"
            f"1 {question['question']}", 
            reply_markup=keyboard
        )
    else:
        await state.set_state(TestStates.waiting_for_answer)
        await state.update_data(current_question=0, answers={})
        
        # Birinchi savolni yuborish
        question = FRIENDSHIP_TEST_QUESTIONS[0]
        keyboard = get_inline_keyboard(question['options'])
        
        await message.answer(
            " Salom! Keling, do'stlaringiz uchun test yaratamiz.\n"
            "Avval siz savollarga javob bering, keyin do'stlaringiz ham javob beradi.\n\n"
            f"1 {question['question']}", 
            reply_markup=keyboard
        )

@dp.callback_query(lambda c: c.data.startswith("answer:"))
async def process_answer(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    
    data = await state.get_data()
    current_question = data.get('current_question', 0)
    answers = data.get('answers', {})
    
    # Joriy javobni saqlash
    answer_index = int(callback.data.split(":")[1])
    answers[current_question] = FRIENDSHIP_TEST_QUESTIONS[current_question]['options'][answer_index]
    
    # Keyingi savolga o'tish
    current_question += 1
    
    if current_question < len(FRIENDSHIP_TEST_QUESTIONS):
        # Keyingi savolni yuborish
        question = FRIENDSHIP_TEST_QUESTIONS[current_question]
        keyboard = get_inline_keyboard(question['options'])
        
        question_number = ["1", "2", "3", "4", "5"][current_question]
        
        await state.update_data(current_question=current_question, answers=answers)
        await callback.message.edit_text(
            f"{question_number} {question['question']}", 
            reply_markup=keyboard
        )
    else:
        # Test yakunlandi, linkni yaratish
        test_id = f"test_{callback.from_user.id}_{random.randint(1000, 9999)}"
        
        # Testni bazaga saqlash
        if not db.save_test(test_id, callback.from_user.id, answers):
            await callback.message.edit_text(" Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")
            return
        
        share_text = f" Do'stlik testi!\n\nKeling, bilimingizni sinab ko'ramiz! Qani ko'raylik-chi, meni qanchalik yaxshi bilasiz?\n\n https://t.me/htcgcutcfbot?start={test_id}"
        
        share_button = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=" Do'stlarga yuborish",
                switch_inline_query=share_text
            )]
        ])
        
        await state.clear()
        await callback.message.edit_text(
            " Sizning testingiz tayyor! Endi do'stlaringiz bilan ulashing.\n\n"
            " Do'stlaringiz javob berganida, men sizga natijalarni yuboraman.\n\n"
            f" Test linki: https://t.me/htcgcutcfbot?start={test_id}",
            reply_markup=share_button
        )

@dp.callback_query(lambda c: c.data.startswith("friend_answer:"))
async def process_friend_answer(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    
    data = await state.get_data()
    test_id = data.get('test_id')
    current_question = data.get('current_question', 0)
    answers = data.get('answers', {})
    
    # Joriy javobni saqlash
    answer_index = int(callback.data.split(":")[1])
    answers[current_question] = FRIENDSHIP_TEST_QUESTIONS[current_question]['options'][answer_index]
    
    # Keyingi savolga o'tish
    current_question += 1
    
    if current_question < len(FRIENDSHIP_TEST_QUESTIONS):
        # Keyingi savolni yuborish
        question = FRIENDSHIP_TEST_QUESTIONS[current_question]
        keyboard = get_inline_keyboard(question['options'], "friend_answer")
        
        question_number = ["1", "2", "3", "4", "5"][current_question]
        
        await state.update_data(current_question=current_question, answers=answers)
        await callback.message.edit_text(
            f"{question_number} {question['question']}", 
            reply_markup=keyboard
        )
    else:
        # Test yakunlandi, natijalarni hisoblash
        test_data = db.get_test(test_id)
        creator_answers = test_data['creator_answers']
        
        # To'g'ri javoblar sonini hisoblash
        correct_count = sum(1 for q in range(len(FRIENDSHIP_TEST_QUESTIONS))
                          if answers.get(q) == creator_answers.get(str(q)))
        
        percentage = (correct_count / len(FRIENDSHIP_TEST_QUESTIONS)) * 100
        
        # Natijalarni bazaga saqlash
        db.save_participant(test_id, callback.from_user.id, answers, correct_count)
        
        # Foydalanuvchiga natijani ko'rsatish
        await callback.message.edit_text(
            f"🎉 Test yakunlandi!\n\n"
            f"📊 Natija: {correct_count}/{len(FRIENDSHIP_TEST_QUESTIONS)} "
            f"({percentage:.1f}%)\n\n"
            "🎨 Sertifikat olish uchun ismingizni kiriting:"
        )
        
        # Test yaratuvchisiga xabar yuborish
        creator_message = (
            f"🎯 Kimdir sizning do'stlik testingizni yakunladi!\n\n"
            f"📊 Natija: {correct_count}/{len(FRIENDSHIP_TEST_QUESTIONS)} "
            f"({percentage:.1f}%)\n"
            f"👤 Foydalanuvchi: @{callback.from_user.username or 'username_yoq'}\n"
            f"👋 Ismi: {callback.from_user.full_name}\n\n"
            "Javoblar:\n"
        )
        
        for i, (user_answer, correct_answer) in enumerate(zip(answers.values(), creator_answers.values())):
            question = FRIENDSHIP_TEST_QUESTIONS[i]['question']
            emoji = "✅" if user_answer == correct_answer else "❌"
            creator_message += f"\n{emoji} {question}\n"
            creator_message += f"Javob: {user_answer}\n"
            
        await bot.send_message(test_data['creator_id'], creator_message)
        
        await state.set_state(TestStates.waiting_for_name)
        await state.update_data(test_id=test_id, correct_count=correct_count)

def create_certificate(name: str, correct_count: int, total_questions: int, percentage: float) -> str:
    """Sertifikat yaratish"""
    try:
        # Asosiy rasm yaratish
        width, height = 1200, 800
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)
        
        # Ramka chizish
        draw.rectangle([(40, 40), (width-40, height-40)], outline='gold', width=5)
        draw.rectangle([(50, 50), (width-50, height-50)], outline='gold', width=2)
        
        try:
            font_path = "OpenSans-Bold.ttf"
            title_font = ImageFont.truetype(font_path, 60)
            main_font = ImageFont.truetype(font_path, 40)
            date_font = ImageFont.truetype(font_path, 30)
        except Exception as e:
            print(f"Shrift yuklashda xatolik: {e}")
            # Agar shrift topilmasa, default shriftni ishlatamiz
            title_font = ImageFont.load_default()
            main_font = ImageFont.load_default()
            date_font = ImageFont.load_default()
        
        # Sarlavha
        draw.text((width//2, 150), "DO'STLIK SERTIFIKATI", 
                 font=title_font, fill='navy', anchor="mm")
        
        # Ism
        draw.text((width//2, 300), f"{name}", 
                 font=main_font, fill='black', anchor="mm")
        
        # Natija
        result_text = f"Do'stlik testida {total_questions} ta savoldan"
        draw.text((width//2, 400), result_text, 
                 font=main_font, fill='black', anchor="mm")
        
        result_text2 = f"{correct_count} ta to'g'ri javob berdi"
        draw.text((width//2, 460), result_text2, 
                 font=main_font, fill='black', anchor="mm")
        
        # Foiz
        percentage_text = f"Natija: {percentage:.1f}%"
        draw.text((width//2, 540), percentage_text, 
                 font=main_font, fill='navy', anchor="mm")
        
        # Daraja
        if percentage >= 80:
            level = "🌟 OLTIN DARAJA 🌟"
            level_desc = "Siz ajoyib do'stsiz!"
        elif percentage >= 60:
            level = "✨ KUMUSH DARAJA ✨"
            level_desc = "Siz yaxshi do'stsiz!"
        else:
            level = "💫 BRONZA DARAJA 💫"
            level_desc = "Siz yangi do'stsiz!"
        
        draw.text((width//2, 600), level, 
                 font=main_font, fill='darkred', anchor="mm")
        draw.text((width//2, 660), level_desc, 
                 font=main_font, fill='darkred', anchor="mm")
        
        # Sana
        current_date = datetime.now().strftime("%d.%m.%Y")
        draw.text((width-100, height-100), current_date, 
                 font=date_font, fill='black', anchor="mm")
        
        # Vaqtinchalik fayl yaratish
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
        image.save(temp_file.name)
        return temp_file.name
        
    except Exception as e:
        print(f"Sertifikat yaratishda xatolik: {e}")
        return None

@dp.message(TestStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    results = data.get('test_results')
    
    if not results:
        await message.answer("❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")
        return
    
    # Sertifikat yaratish
    cert_path = create_certificate(
        name=message.text,
        correct_count=results['correct_answers'],
        total_questions=results['total_questions'],
        percentage=results['percentage']
    )
    
    if cert_path and os.path.exists(cert_path):
        try:
            # Sertifikatni yuborish
            await message.answer_photo(
                photo=FSInputFile(cert_path),
                caption="🎉 Tabriklaymiz! Sizning do'stlik sertifikatingiz tayyor!\n"
                       "🔄 Yana bir bor sinab ko'rish uchun /start bosing."
            )
        finally:
            # Sertifikatni o'chirish
            try:
                os.remove(cert_path)
            except Exception as e:
                print(f"Faylni o'chirishda xatolik: {e}")
    else:
        await message.answer(
            "❌ Sertifikat yaratishda xatolik yuz berdi.\n"
            "🔄 Yana bir bor sinab ko'rish uchun /start bosing."
        )
    
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    import logging

    logging.basicConfig(level=logging.INFO)

    asyncio.run(main())
