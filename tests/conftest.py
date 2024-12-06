import pytest
import asyncio
from pathlib import Path
from bot import init_db

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
async def setup_database():
    """Setup test database before each test."""
    Path("data").mkdir(exist_ok=True)
    await init_db()
    yield
    # Cleanup after tests
    try:
        Path("data/recipes.db").unlink()
    except FileNotFoundError:
        pass