import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from sqlalchemy import String, Integer, DateTime, select, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, Mapped, mapped_column

# Create async engine
engine = create_async_engine("sqlite+aiosqlite:///data/recipes.db", echo=False)

# Create async session factory
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Create declarative base
Base = declarative_base()


class Recipe(Base):
    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String)
    text: Mapped[str] = mapped_column(String)
    image: Mapped[str] = mapped_column(String)
    video: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


async def init_db():
    Path("data").mkdir(exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        return session


async def add_user(user_id: int) -> None:
    async with async_session() as session:
        exist_user = await session.execute(select(User).where(User.user_id == user_id))
        logging.info("exist_user = %s", exist_user)
        if exist_user.scalar_one_or_none():
            return
        user = User(user_id=user_id)
        session.add(user)
        await session.commit()


async def get_one_user(user_id: int) -> Optional[User]:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        return result.scalar_one_or_none()


async def get_all_users() -> List[int]:
    async with async_session() as session:
        result = await session.execute(select(User.user_id))
        return [row[0] for row in result.fetchall()]


async def add_recipe(
    title: str, text: str, image: str, video: Optional[str] = None
) -> Recipe:
    async with async_session() as session:
        recipe = Recipe(title=title, text=text, image=image, video=video)
        session.add(recipe)
        await session.commit()
        return recipe


async def get_recipe(recipe_id: int) -> Optional[Recipe]:
    async with async_session() as session:
        result = await session.execute(select(Recipe).where(Recipe.id == recipe_id))
        return result.scalar_one_or_none()


async def get_all_recipes() -> List[Recipe]:
    async with async_session() as session:
        result = await session.execute(select(Recipe))
        return result.scalars().all()


async def update_recipe(
    recipe_id: int, title: str, text: str, image: str, video: Optional[str] = None
) -> Optional[Recipe]:
    async with async_session() as session:
        recipe = await session.get(Recipe, recipe_id)
        if recipe:
            recipe.title = title
            recipe.text = text
            recipe.image = image
            recipe.video = video
            await session.commit()
        return recipe


async def delete_recipe(recipe_id: int) -> bool:
    async with async_session() as session:
        result = await session.execute(delete(Recipe).where(Recipe.id == recipe_id))
        await session.commit()
        return result.rowcount > 0
