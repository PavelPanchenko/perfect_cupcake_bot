import asyncio
import logging
import random

from aiogram import Router, types
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.types import InputMediaPhoto, InputMediaVideo
from aiogram.utils.payload import decode_payload

from ..config import settings
from ..database import get_all_recipes, get_one_user, add_user

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

user_router = Router()

MESSAGE_WELCOME = (
    # "👋 Добро пожаловать в кулинарный бот!\n"
    # "Здесь вы найдете множество вкусных рецептов.\n\n"
    # "Команды:\n"
    # "/recipe - Получить случайный рецепт\n"
    # "/all_recipes - Получить все рецепты\n"
    # "/start - Начать работу с ботом"
    "👋 Ласкаво просимо до кулінарного боту!\n"
    "Тут ви знайдете безліч смачних рецептів.\n\n"
    "Команди:\n"
    "/recipe - Отримати випадковий рецепт\n"
    "/all_recipes - Отримати всі рецепти\n"
    "/start - Почати роботу з ботом"
)


@user_router.message(CommandStart(deep_link=True))
async def cmd_start_with_deep_link(message: types.Message, command: CommandObject):
    user_id = message.from_user.id

    await add_user(user_id)

    verify_deep_link = command.args
    payload = decode_payload(verify_deep_link)

    if not payload:
        return
    if payload != settings.VALID_CODE:
        return
    for note in settings.WELCOME_VIDEO_NOTES:
        await message.answer_video_note(note, protect_content=True)
        await asyncio.sleep(2)
    await message.answer(
        MESSAGE_WELCOME,
    )


@user_router.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id

    user = await get_one_user(user_id)
    if not user:
        return
    await message.answer(MESSAGE_WELCOME)


@user_router.message(Command("all_recipes"))
async def cmd_all_recipes(message: types.Message):
    recipes = await get_all_recipes()
    if not recipes:
        await message.answer("Пока нет доступных рецептов.")
        return

    for recipe in recipes:
        if recipe.video:
            media = [
                InputMediaPhoto(
                    media=recipe.image,
                    caption=f"🍳 {recipe.title}\n\n{recipe.text}",
                    caption_entities=message.entities,
                ),
                InputMediaVideo(
                    media=recipe.video,
                    caption=f"🍳 {recipe.title}\n\n{recipe.text}",
                    caption_entities=message.entities,
                ),
            ]
            await message.answer_media_group(media, protect_content=True)
        else:
            await message.answer_photo(
                photo=recipe.image,
                caption=f"🍳 {recipe.title}\n\n{recipe.text}",
                caption_entities=message.entities,
                protect_content=True,
            )
        await asyncio.sleep(0.5)  # Prevent flood limits


@user_router.message(Command("recipe"))
async def cmd_random_recipe(message: types.Message):
    """Send a random recipe to the user"""
    recipes = await get_all_recipes()
    if not recipes:
        await message.answer("Пока нет доступных рецептов.")
        return

    recipe = random.choice(recipes)
    if recipe.video:
        media = [
            InputMediaPhoto(
                media=recipe.image, caption=f"🍳 {recipe.title}\n\n{recipe.text}"
            ),
            InputMediaVideo(
                media=recipe.video, caption=f"🍳 {recipe.title}\n\n{recipe.text}"
            ),
        ]

        await message.answer_media_group(media, protect_content=True)
    else:
        await message.answer_photo(
            photo=recipe.image,
            caption=f"🍳 {recipe.title}\n\n{recipe.text}",
            protect_content=True,
        )
