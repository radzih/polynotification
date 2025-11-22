from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from fluentogram import TranslatorHub

class I18nMiddleware(BaseMiddleware):
    def __init__(self, translator_hub: TranslatorHub):
        self.translator_hub = translator_hub

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Hardcoded to 'uk' for now as requested
        data["i18n"] = self.translator_hub.get_translator_by_locale("uk")
        return await handler(event, data)
