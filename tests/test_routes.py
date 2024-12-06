import pytest
from unittest.mock import AsyncMock, patch
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, User as TelegramUser, Chat
from bot.routes.user import user_router
from bot.routes.admin import admin_router
from bot.routes.recipes import recipe_router
from bot.config import ADMIN_ID

@pytest.fixture
def bot():
    return AsyncMock(spec=Bot)

@pytest.fixture
def dp(bot):
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_router(user_router)
    dp.include_router(admin_router)
    dp.include_router(recipe_router)
    return dp

@pytest.fixture
def message(bot):
    message = AsyncMock(spec=Message)
    message.bot = bot
    message.from_user = AsyncMock(spec=TelegramUser)
    message.chat = AsyncMock(spec=Chat)
    return message

@pytest.mark.asyncio
async def test_start_command(message, dp):
    message.text = "/start"
    message.from_user.id = 12345
    
    await dp.feed_update(message)
    
    message.answer.assert_called_once()
    assert "Добро пожаловать" in message.answer.call_args[0][0]

@pytest.mark.asyncio
async def test_admin_command_not_admin(message, dp):
    message.text = "/admin"
    message.from_user.id = 12345  # Not admin
    
    await dp.feed_update(message)
    
    message.answer.assert_not_called()

@pytest.mark.asyncio
async def test_admin_command_is_admin(message, dp):
    message.text = "/admin"
    message.from_user.id = ADMIN_ID
    
    await dp.feed_update(message)
    
    message.answer.assert_called_once()
    assert "Команды администратора" in message.answer.call_args[0][0]

@pytest.mark.asyncio
async def test_all_recipes_empty(message, dp):
    message.text = "/all_recipes"
    
    with patch('bot.routes.user.get_all_recipes', return_value=[]):
        await dp.feed_update(message)
        
        message.answer.assert_called_once_with("Пока нет доступных рецептов.")