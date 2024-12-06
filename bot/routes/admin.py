import asyncio
import logging

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.deep_linking import create_start_link

from ..config import settings
from ..database import (
    get_all_users,
    get_all_recipes,
    add_recipe,
    update_recipe,
    delete_recipe,
    get_recipe,
)

admin_router = Router()


class RecipeStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_text = State()
    waiting_for_image = State()
    waiting_for_video = State()
    confirm_delete = State()
    select_recipe = State()
    select_field = State()
    edit_field = State()


recipe_data = {}


def is_admin(message: types.Message) -> bool:
    return message.from_user.id in settings.ADMIN_IDS


@admin_router.message(Command("admin"))
async def cmd_admin_help(message: types.Message, state: FSMContext):
    if not is_admin(message):
        await message.answer("Вы не администратор.")
        return

    await state.clear()
    help_text = """
🔑 Команды администратора:

/add_recipe - Добавить новый рецепт
/edit_recipe - Редактировать существующий рецепт
/delete_recipe - Удалить рецепт
/list_recipes - Список всех рецептов
/broadcast - Отправить сообщение всем пользователям
/stats - Статистика пользователей
/get_deep_link - Получить ссылку на бот
"""
    await message.answer(help_text)


# Добавление рецептов
@admin_router.message(Command("add_recipe"))
async def cmd_add_recipe(message: types.Message, state: FSMContext):
    """Start the recipe addition process"""
    if not is_admin(message):
        return

    recipe_data.clear()
    await message.answer("Введите название рецепта:")
    await state.set_state(RecipeStates.waiting_for_title)


@admin_router.message(RecipeStates.waiting_for_title)
async def process_title(message: types.Message, state: FSMContext):
    """Process the recipe title"""
    recipe_data["title"] = message.text
    await message.answer("Введите текст рецепта:")
    await state.set_state(RecipeStates.waiting_for_text)


@admin_router.message(RecipeStates.waiting_for_text)
async def process_text(message: types.Message, state: FSMContext):
    """Process the recipe text"""
    recipe_data["text"] = message.text
    await message.answer("Отправьте фото блюда:")
    await state.set_state(RecipeStates.waiting_for_image)


@admin_router.message(RecipeStates.waiting_for_image)
async def process_image(message: types.Message, state: FSMContext):
    """Process the recipe image"""
    if not message.photo:
        await message.answer("Пожалуйста, отправьте фото.")
        return

    recipe_data["image"] = message.photo[-1].file_id
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да", callback_data="add_video"),
                InlineKeyboardButton(text="Нет", callback_data="skip_video"),
            ]
        ]
    )
    await message.answer("Хотите добавить видео?", reply_markup=keyboard)
    await state.set_state(RecipeStates.waiting_for_video)


@admin_router.callback_query(RecipeStates.waiting_for_video, F.data == "add_video")
async def request_video(callback: types.CallbackQuery):
    """Request video from admin"""
    await callback.message.answer("Отправьте видео:")


@admin_router.callback_query(RecipeStates.waiting_for_video, F.data == "skip_video")
async def skip_video(callback: types.CallbackQuery, state: FSMContext):
    """Skip video addition and finish recipe creation"""
    await finish_recipe_creation(callback.message, state)


@admin_router.message(RecipeStates.waiting_for_video)
async def process_video(message: types.Message, state: FSMContext):
    """Process the recipe video"""
    if message.video_note:
        recipe_data["video"] = message.video_note.file_id
    if message.video:
        recipe_data["video"] = message.video.file_id
    await finish_recipe_creation(message, state)


async def finish_recipe_creation(message: types.Message, state: FSMContext):
    """Finish recipe creation and save to database"""
    recipe = await add_recipe(
        title=recipe_data["title"],
        text=recipe_data["text"],
        image=recipe_data["image"],
        video=recipe_data.get("video"),
    )

    await message.answer(
        f"✅ Рецепт успешно добавлен!\n\n"
        f"📝 Название: {recipe.title}\n"
        f"📋 Описание: {recipe.text}"
    )
    await state.clear()


####


@admin_router.message(Command("list_recipes"))
async def cmd_list_recipes(message: types.Message):
    """List all available recipes"""
    if not is_admin(message):
        return

    recipes = await get_all_recipes()
    if not recipes:
        await message.answer("Нет доступных рецептов.")
        return

    text = "📋 Список рецептов:\n\n"
    for recipe in recipes:
        text += f"{recipe.id}. {recipe.title}\n"

    await message.answer(text)


###


@admin_router.message(Command("delete_recipe"))
async def cmd_delete_recipe(message: types.Message, state: FSMContext):
    """Start recipe deletion process"""
    if not is_admin(message):
        return

    recipes = await get_all_recipes()
    if not recipes:
        await message.answer("Нет доступных рецептов для удаления.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{r.title}", callback_data=f"delete_{r.id}")]
            for r in recipes
        ]
    )

    await message.answer("Выберите рецепт для удаления:", reply_markup=keyboard)
    await state.set_state(RecipeStates.confirm_delete)


@admin_router.callback_query(RecipeStates.confirm_delete)
async def process_delete_recipe(callback: types.CallbackQuery, state: FSMContext):
    """Process recipe deletion"""
    recipe_id = int(callback.data.split("_")[1])
    success = await delete_recipe(recipe_id)

    if success:
        await callback.message.answer("✅ Рецепт успешно удален!")
    else:
        await callback.message.answer("❌ Ошибка при удалении рецепта.")

    await state.clear()


####


@admin_router.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message):
    if not is_admin(message):
        return

    text = message.text.replace("/broadcast ", "", 1)
    users = await get_all_users()

    for user_id in users:
        try:
            await message.bot.send_message(user_id, text)
            await asyncio.sleep(0.1)
        except Exception as e:
            logging.error(f"Failed to send message to {user_id}: {e}")

    await message.answer("Рассылка завершена!")


@admin_router.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if not is_admin(message):
        return

    users = await get_all_users()
    recipes = await get_all_recipes()

    stats = f"""📊 Статистика бота:

👥 Всего пользователей: {len(users)}
📝 Всего рецептов: {len(recipes)}"""

    await message.answer(stats)


@admin_router.message(Command("edit_recipe"))
async def cmd_edit_recipe(message: types.Message, state: FSMContext):
    """Start recipe editing process"""
    if not is_admin(message):
        return

    recipes = await get_all_recipes()
    if not recipes:
        await message.answer("Нет доступных рецептов для редактирования.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{r.title}", callback_data=f"edit_{r.id}")]
            for r in recipes
        ]
    )

    await message.answer("Выберите рецепт для редактирования:", reply_markup=keyboard)
    await state.set_state(RecipeStates.select_recipe)


@admin_router.callback_query(RecipeStates.select_recipe)
async def process_recipe_selection(callback: types.CallbackQuery, state: FSMContext):
    """Process recipe selection for editing"""
    recipe_id = int(callback.data.split("_")[1])
    recipe = await get_recipe(recipe_id)

    if not recipe:
        await callback.message.answer("Рецепт не найден.")
        await state.clear()
        return

    await state.update_data(recipe_id=recipe_id)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Название", callback_data="edit_title")],
            [InlineKeyboardButton(text="Описание", callback_data="edit_text")],
            [InlineKeyboardButton(text="Фото", callback_data="edit_image")],
            [InlineKeyboardButton(text="Видео", callback_data="edit_video")],
        ]
    )

    await callback.message.answer(
        f"Текущий рецепт:\n\n"
        f"📝 Название: {recipe.title}\n"
        f"📋 Описание: {recipe.text}\n\n"
        f"Выберите, что хотите отредактировать:",
        reply_markup=keyboard,
    )
    await state.set_state(RecipeStates.select_field)


@admin_router.callback_query(RecipeStates.select_field)
async def process_field_selection(callback: types.CallbackQuery, state: FSMContext):
    """Process field selection for editing"""
    field = callback.data.split("_")[1]
    await state.update_data(edit_field=field)

    messages = {
        "title": "Введите новое название рецепта:",
        "text": "Введите новое описание рецепта:",
        "image": "Отправьте новое фото рецепта:",
        "video": "Отправьте новое видео рецепта (кружочком):",
    }

    await callback.message.answer(messages[field])
    await state.set_state(RecipeStates.edit_field)


@admin_router.message(RecipeStates.edit_field)
async def process_field_update(message: types.Message, state: FSMContext):
    """Process field update"""
    data = await state.get_data()
    recipe_id = data["recipe_id"]
    field = data["edit_field"]

    recipe = await get_recipe(recipe_id)
    if not recipe:
        await message.answer("Рецепт не найден.")
        await state.clear()
        return

    # Prepare updated data
    update_data = {
        "title": recipe.title,
        "text": recipe.text,
        "image": recipe.image,
        "video": recipe.video,
    }

    # Update specific field
    if field == "title":
        update_data["title"] = message.text
    elif field == "text":
        update_data["text"] = message.text
    elif field == "image":
        if not message.photo:
            await message.answer("Пожалуйста, отправьте фото.")
            return
        update_data["image"] = message.photo[-1].file_id
    elif field == "video":
        if not message.video_note:
            await message.answer("Пожалуйста, отправьте видео кружочком.")
            return
        update_data["video"] = message.video_note.file_id

    # Update recipe
    updated_recipe = await update_recipe(recipe_id=recipe_id, **update_data)

    if updated_recipe:
        await message.answer(
            f"✅ Рецепт успешно обновлен!\n\n"
            f"📝 Название: {updated_recipe.title}\n"
            f"📋 Описание: {updated_recipe.text}"
        )
    else:
        await message.answer("❌ Ошибка при обновлении рецепта.")

    await state.clear()


@admin_router.message(Command("get_deep_link"))
async def cmd_get_deep_link(message: types.Message):
    if not is_admin(message):
        return
    deep_link = await create_start_link(message.bot, settings.VALID_CODE, encode=True)
    await message.answer(f"Deep link: {deep_link}")
