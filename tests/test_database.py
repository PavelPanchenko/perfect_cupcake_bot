import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from bot.database import (
    Base,
    add_recipe,
    get_recipe,
    update_recipe,
    delete_recipe,
)


@pytest.fixture
async def engine():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def session(engine):
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.mark.asyncio
async def test_add_recipe(session):
    recipe = await add_recipe(
        title="Test Recipe", text="Test Description", image="test_image.jpg"
    )
    assert recipe.title == "Test Recipe"
    assert recipe.text == "Test Description"
    assert recipe.image == "test_image.jpg"
    assert recipe.video is None


@pytest.mark.asyncio
async def test_get_recipe(session):
    # Add test recipe
    recipe = await add_recipe(
        title="Test Recipe", text="Test Description", image="test_image.jpg"
    )

    # Get recipe
    retrieved = await get_recipe(recipe.id)
    assert retrieved.title == "Test Recipe"
    assert retrieved.text == "Test Description"


@pytest.mark.asyncio
async def test_update_recipe(session):
    # Add test recipe
    recipe = await add_recipe(
        title="Original Title", text="Original Text", image="original_image.jpg"
    )

    # Update recipe
    updated = await update_recipe(
        recipe_id=recipe.id,
        title="Updated Title",
        text="Updated Text",
        image="updated_image.jpg",
        video="video.mp4",
    )

    assert updated.title == "Updated Title"
    assert updated.text == "Updated Text"
    assert updated.image == "updated_image.jpg"
    assert updated.video == "video.mp4"


@pytest.mark.asyncio
async def test_delete_recipe(session):
    # Add test recipe
    recipe = await add_recipe(
        title="Test Recipe", text="Test Description", image="test_image.jpg"
    )

    # Delete recipe
    success = await delete_recipe(recipe.id)
    assert success is True

    # Verify deletion
    deleted = await get_recipe(recipe.id)
    assert deleted is None
