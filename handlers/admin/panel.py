from aiogram.fsm.context import FSMContext
from aiogram import types, F
from aiogram.filters import Command

from filters.admin_bot import IsBotAdmin
from keyboards.default.buttons import (
    admin_button, film_delete_or_join, serial_delete_or_join,
    majburiy_obuna, add_admin
)
from handlers.admin import admin_router
from loader import db


@admin_router.message(Command('admin'), IsBotAdmin())
async def start_admin_bot(message: types.Message):
    await message.answer("🔝 Admin panel....", reply_markup=admin_button())


@admin_router.message(F.text == "📀 Kino joylash / O'chrish", IsBotAdmin())
async def delete_or_join(message: types.Message, state: FSMContext):
    await message.answer("📀 Kino joylash / O'chrish bo'limi !", reply_markup=film_delete_or_join())


@admin_router.message(F.text == "📽 Seril joylash / O'chrish", IsBotAdmin())
async def serial_section(message: types.Message, state: FSMContext):
    await message.answer("📽 Seril joylash / O'chrish bo'limi !", reply_markup=serial_delete_or_join())


@admin_router.message(F.text == "🛎 Obunachilar soni", IsBotAdmin())
async def member(message: types.Message):
    count_result = db.count_users()
    count = count_result['total']
    await message.answer(f"👥  Foydalanuvchilar soni: {count}", reply_markup=admin_button())


@admin_router.message(F.text == "📌Majburiy Obuna", IsBotAdmin())
async def force_channel(message: types.Message):
    await message.answer("🔝 Majburiy obunalar qo'shish bo'limi:", reply_markup=majburiy_obuna())


@admin_router.message(F.text == "🤵🏻‍♂️ Admin qo'shish / o'chrish", IsBotAdmin())
async def admin_section(message: types.Message):
    await message.answer("🔝 Admin qo'shish bo'limi:", reply_markup=add_admin())


@admin_router.message(F.text == "🔙 Orqaga", IsBotAdmin())
async def orqaga(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🔝 Asosiy Menyu", reply_markup=admin_button())


@admin_router.message(F.text == "🔝 Asosiy admin panelga qaytish", IsBotAdmin())
async def orqaga_asosiy(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🔝 Asosiy Menyu", reply_markup=admin_button())
