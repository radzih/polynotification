import re
import logging
from dataclasses import asdict

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram_dialog import DialogManager, StartMode
from fluentogram import TranslatorRunner

from src.presentation.states import AddMarketSG, MarketListSG
from src.use_cases.market.add import POLYMARKET_URL_PATTERN
from src.use_cases.market.check_exists import CheckMarketExistsUseCase
from src.use_cases.market.get_event_markets import GetEventMarketsUseCase
from src.use_cases.market.toggle_monitoring import ToggleMonitoringUseCase
from src.domain.exceptions import MarketNotFoundError, MarketApiError

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text.regexp(POLYMARKET_URL_PATTERN))
async def market_url_handler(
    message: Message,
    dialog_manager: DialogManager,
    check_market_exists_use_case: CheckMarketExistsUseCase,
    get_event_markets_use_case: GetEventMarketsUseCase,
    i18n: TranslatorRunner,
):
    url = message.text.strip()
    match = re.search(POLYMARKET_URL_PATTERN, url)
    slug = match.group(1)
    event_url = f"https://polymarket.com/event/{slug}"
    
    try:
        markets = await get_event_markets_use_case(slug)
    except (MarketNotFoundError, MarketApiError) as e:
        await message.answer(i18n.err_event_fetch(error=str(e)))
        return

    if not markets:
        await message.answer(i18n.err_no_markets())
        return

    if len(markets) == 1:
        market_id = markets[0].id
        
        # Check if market already exists
        existing_market = await check_market_exists_use_case(message.from_user.id, market_id)
        
        if existing_market:
            await dialog_manager.start(
                AddMarketSG.market_exists,
                mode=StartMode.RESET_STACK,
                data={"existing_market_id": existing_market.id}
            )
        else:
            # Pass the full URL and market_id to the dialog start data
            await dialog_manager.start(
                AddMarketSG.selecting_price,
                mode=StartMode.RESET_STACK,
                data={"url": event_url, "market_id": market_id}
            )
    else:
        # Multiple markets
        # Convert DTOs to dicts for safe serialization
        markets_data = [asdict(m) for m in markets]
        await dialog_manager.start(
            AddMarketSG.selecting_market,
            mode=StartMode.RESET_STACK,
            data={"url": event_url, "markets": markets_data}
        )


@router.message(Command("add"))
async def add_market_command(
    message: Message,
    dialog_manager: DialogManager,
    i18n: TranslatorRunner,
):
    await message.answer(i18n.add_market_prompt_url())


@router.message(Command("markets"))
async def list_markets_handler(message: Message, dialog_manager: DialogManager):
    await dialog_manager.start(
        MarketListSG.list,
        mode=StartMode.RESET_STACK,
    )


@router.callback_query(F.data.startswith("enable_mon:"))
async def enable_monitoring_callback(
    callback: CallbackQuery,
    toggle_monitoring_use_case: ToggleMonitoringUseCase,
    i18n: TranslatorRunner,
):
    market_id = int(callback.data.split(":")[1])
    
    logger.info(f"Re-enabling monitoring for market {market_id}")
    
    # Re-enable monitoring
    updated_market = await toggle_monitoring_use_case(market_id, is_active=True)
    
    if updated_market:
        await callback.answer(i18n.monitoring_reenabled_alert())
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
            await callback.message.reply(i18n.monitoring_reenabled_message())
        except Exception as e:
            logger.error(f"Failed to update message: {e}")
    else:
        await callback.answer(i18n.monitoring_reenable_failed(), show_alert=True)
