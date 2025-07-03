import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from intentkit.models.db import init_db
from intentkit.models.redis import init_redis
from app.chat.router import router_rw as chat_router_rw, router_ro as chat_router_ro
from app.agent.router import router_rw as agent_router_rw, router_ro as agent_router_ro
from app.config import config

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle.

    This context manager:
    1. Initializes database connection
    2. Performs any necessary startup tasks
    3. Handles graceful shutdown

    Args:
        app: FastAPI application instance
    """
    # Initialize database
    await init_db(**config.db)

    # Initialize Redis if configured
    if config.redis_host:
        await init_redis(
            host=config.redis_host,
            port=config.redis_port,
        )

    logger.info("API server start")
    yield
    # Clean up will run after the API server shutdown
    logger.info("Cleaning up and shutdown...")


app = FastAPI(
    title="Nation IntentKit API",
    description="API for Nation IntentKit services",
    version=config.release,
    lifespan=lifespan,
)

app.include_router(chat_router_rw)
app.include_router(chat_router_ro)
app.include_router(agent_router_rw)
app.include_router(agent_router_ro)
