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

MESSAGE_COMMAND = (
    # "👋 Добро пожаловать в кулинарный бот!\n"
    # "Здесь вы найдете множество вкусных рецептов.\n\n"
    # "Команды:\n"
    # "/recipe - Получить случайный рецепт\n"
    # "/all_recipes - Получить все рецепты\n"
    # "/start - Начать работу с ботом"
    "Що можно зробити:\n"
    "/recipe - Отримати випадковий рецепт\n"
    "/all_recipes - Отримати всі рецепти\n"
)

MESSAGE_WELCOME_BIG = (
    "Привіт, друзі! 👩‍🍳👨‍🍳\n\n"
    "Радий вітати вас на моєму курсі “Секрет ідеального кексу”.\n\n"
    "На цьому курсі ви отримаєте:\n"
    "✅ Детальні покрокові рецепти, які гарантовано допоможуть створити кекси вашої мрії.\n"
    "✅ Цінні поради, як уникнути поширених помилок у випічці.\n"
    "✅ Інформацію про найкращі інгредієнти та техніки для приготування повітряних, смачних кексів.\n"
    "✅ Інтерактивну підтримку через мою Instagram-сторінку @svitlychnyi_chef – я завжди на зв’язку, щоб відповісти на ваші питання.\n\n"
    "Мій курс створений так, щоб навіть новачки легко могли почати. Усе просто, зрозуміло і з любов’ю до кулінарії!\n\n"
    "🌟 Переходьте до матеріалів, пробуйте, експериментуйте – і ваші кекси стануть зірками кожного столу!\n\n"
    "Бажаю вам натхнення і смачної випічки!"
)


# @user_router.message()
# async def get_file_id(message: types.Message):
#     if message.document:
#         await message.answer(message.document.file_id)
#     elif message.photo:
#         await message.answer(message.photo[-1].file_id)
#     elif message.video:
#         await message.answer(message.video.file_id)


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

    await message.answer(MESSAGE_WELCOME_BIG)
    await asyncio.sleep(0.5)
    for note in settings.WELCOME_VIDEO_NOTES:
        await message.answer_video_note(note, protect_content=True)
        await asyncio.sleep(2)
    await message.answer(
        MESSAGE_COMMAND,
    )


@user_router.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id

    user = await get_one_user(user_id)
    if not user:
        return
    await message.answer(MESSAGE_COMMAND)


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
                    # show_caption_above_media=True,
                ),
                InputMediaVideo(
                    media=recipe.video,
                    # caption=f"🍳 {recipe.title}\n\n{recipe.text}",
                    # caption_entities=message.entities,
                    # show_caption_above_media=True,
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
                media=recipe.image,
                caption=f"🍳 {recipe.title}\n\n{recipe.text}",
                # show_caption_above_media=True,
            ),
            InputMediaVideo(
                media=recipe.video,
                # caption=f"🍳 {recipe.title}\n\n{recipe.text}",
                # show_caption_above_media=True,
            ),
        ]

        await message.answer_media_group(media, protect_content=True)
    else:
        await message.answer_photo(
            photo=recipe.image,
            caption=f"🍳 {recipe.title}\n\n{recipe.text}",
            protect_content=True,
        )
