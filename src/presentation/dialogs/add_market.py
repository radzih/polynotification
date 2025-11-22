import operator
from typing import Any
from dataclasses import asdict

from aiogram.types import CallbackQuery, Message, User
from aiogram_dialog import Dialog, DialogManager, Window, StartMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Column, Group, Cancel, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format
from fluentogram import TranslatorRunner

from src.presentation.states import AddMarketSG, MarketListSG
from src.use_cases.market.add import AddMarketUseCase
from src.use_cases.market.check_exists import CheckMarketExistsUseCase
from src.domain.exceptions import MarketAlreadyExistsError


async def on_dialog_start(start_data: dict, manager: DialogManager):
    if start_data:
        if "existing_market_id" in start_data:
            manager.dialog_data["existing_market_id"] = start_data["existing_market_id"]
        if "url" in start_data:
            manager.dialog_data["url"] = start_data["url"]
        if "market_id" in start_data:
            manager.dialog_data["market_id"] = start_data["market_id"]
        if "markets" in start_data:
            manager.dialog_data["markets"] = start_data["markets"]


async def get_market_options(dialog_manager: DialogManager, **kwargs):
    i18n: TranslatorRunner = dialog_manager.middleware_data["i18n"]
    return {
        "markets": dialog_manager.dialog_data.get("markets", []),
        "text_select_market": i18n.add_market_select(),
        "text_cancel": i18n.common_cancel()
    }


async def get_price_strings(dialog_manager: DialogManager, **kwargs):
    i18n: TranslatorRunner = dialog_manager.middleware_data["i18n"]
    return {
        "text_select_price": i18n.add_market_select_price(),
        "text_cancel": i18n.common_cancel()
    }


async def get_exists_strings(dialog_manager: DialogManager, **kwargs):
    i18n: TranslatorRunner = dialog_manager.middleware_data["i18n"]
    return {
        "text_already_exists": i18n.add_market_already_exists(),
        "text_open_market": i18n.add_market_open_btn(),
        "text_close": i18n.common_close()
    }


async def on_market_option_selected(c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    market_id = item_id
    check_exists: CheckMarketExistsUseCase = manager.middleware_data["check_market_exists_use_case"]
    user_id = c.from_user.id
    
    existing_market = await check_exists(user_id, market_id)
    
    if existing_market:
        manager.dialog_data["existing_market_id"] = existing_market.id
        await manager.switch_to(AddMarketSG.market_exists)
    else:
        manager.dialog_data["market_id"] = market_id
        await manager.switch_to(AddMarketSG.selecting_price)


async def on_price_selected(c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    price = int(item_id)
    await _save_market(manager, price)


async def on_manual_price_input(message: Message, widget: MessageInput, manager: DialogManager):
    i18n: TranslatorRunner = manager.middleware_data["i18n"]
    try:
        price = int(message.text)
        await _save_market(manager, price)
    except ValueError:
        await message.answer(i18n.err_invalid_number())


async def _save_market(manager: DialogManager, price: int):
    add_market_use_case: AddMarketUseCase = manager.middleware_data["add_market_use_case"]
    i18n: TranslatorRunner = manager.middleware_data["i18n"]
    url = manager.dialog_data["url"]
    market_id = manager.dialog_data["market_id"]
    user_id = manager.event.from_user.id
    
    # Notify user we are checking price to set condition
    await manager.event.answer(i18n.add_market_saving())
    
    try:
        await add_market_use_case(
            user_id=user_id, 
            market_id=market_id, 
            market_url=url, 
            target_price=price
        )
        await manager.done()
        
        success_text = i18n.add_market_success(price=price)
        
        if isinstance(manager.event, CallbackQuery):
            try:
                await manager.event.message.edit_text(success_text, reply_markup=None)
            except Exception:
                await manager.event.answer(success_text)
        else:
            await manager.event.answer(success_text)
            
    except MarketAlreadyExistsError as e:
        manager.dialog_data["existing_market_id"] = e.market_id
        await manager.switch_to(AddMarketSG.market_exists)


async def on_open_existing_market(c: CallbackQuery, widget: Any, manager: DialogManager):
    market_id = manager.dialog_data["existing_market_id"]
    await manager.start(
        MarketListSG.view_market,
        data={"selected_market_id": market_id},
        mode=StartMode.RESET_STACK
    )


def get_price_buttons():
    # Generate buttons for 5, 10, ... 95 (exclude 0 and 100)
    prices = [(str(i), str(i)) for i in range(5, 100, 5)]
    return Select(
        Format("{item[0]}%"),
        id="price_select",
        item_id_getter=operator.itemgetter(1),
        items=prices,
        on_click=on_price_selected,
    )


add_market_dialog = Dialog(
    Window(
        Format("{text_select_market}"),
        ScrollingGroup(
            Select(
                Format("{item[question]}"),
                id="market_option",
                item_id_getter=operator.itemgetter("id"),
                items="markets",
                on_click=on_market_option_selected,
            ),
            id="markets_group",
            width=1,
            height=10,
            hide_on_single_page=True,
        ),
        Cancel(Format("{text_cancel}")),
        state=AddMarketSG.selecting_market,
        getter=get_market_options,
    ),
    Window(
        Format("{text_select_price}"),
        Group(
            get_price_buttons(),
            width=4,
        ),
        MessageInput(on_manual_price_input),
        Cancel(Format("{text_cancel}")),
        state=AddMarketSG.selecting_price,
        getter=get_price_strings,
    ),
    Window(
        Format("{text_already_exists}"),
        Button(Format("{text_open_market}"), id="open_existing", on_click=on_open_existing_market),
        Cancel(Format("{text_close}")),
        state=AddMarketSG.market_exists,
        getter=get_exists_strings,
    ),
    on_start=on_dialog_start,
)
