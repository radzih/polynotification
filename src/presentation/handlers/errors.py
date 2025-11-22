import logging

from aiogram import Router
from aiogram.filters import ExceptionTypeFilter
from aiogram.types import ErrorEvent

from src.domain.exceptions import ApplicationException

logger = logging.getLogger(__name__)
router = Router()


@router.error(ExceptionTypeFilter(ApplicationException))
async def app_error_handler(event: ErrorEvent):
    # Log the warning
    logger.warning(f"Application exception: {event.exception}")
    
    # Answer with the exception message
    if event.update.message:
        await event.update.message.answer(str(event.exception))
    elif event.update.callback_query:
        await event.update.callback_query.answer(str(event.exception), show_alert=True)
