import operator
from typing import Any
from dataclasses import asdict

from aiogram.types import CallbackQuery, Message, User
from aiogram_dialog import Dialog, DialogManager, Window, StartMode
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Column, Group, Cancel, ScrollingGroup, Select
from aiogram_dialog.widgets.text import Const, Format

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
    return {"markets": dialog_manager.dialog_data.get("markets", [])}


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
    try:
        price = int(message.text)
        await _save_market(manager, price)
    except ValueError:
        await message.answer("Please enter a valid integer number.")


async def _save_market(manager: DialogManager, price: int):
    add_market_use_case: AddMarketUseCase = manager.middleware_data["add_market_use_case"]
    url = manager.dialog_data["url"]
    market_id = manager.dialog_data["market_id"]
    user_id = manager.event.from_user.id
    
    # Notify user we are checking price to set condition
    await manager.event.answer("Saving market and determining alert condition...")
    
    try:
        await add_market_use_case(
            user_id=user_id, 
            market_id=market_id, 
            market_url=url, 
            target_price=price
        )
        await manager.done()
        
        success_text = f"Market added! Monitoring for price hits at {price}%."
        
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
        Const("Select a market to track:"),
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
        Cancel(Const("Cancel")),
        state=AddMarketSG.selecting_market,
        getter=get_market_options,
    ),
    Window(
        Const("Select target price percentage for notification or enter manually:"),
        Group(
            get_price_buttons(),
            width=4,
        ),
        MessageInput(on_manual_price_input),
        Cancel(Const("Cancel")),
        state=AddMarketSG.selecting_price,
    ),
    Window(
        Const("This market is already in your list."),
        Button(Const("Open Market"), id="open_existing", on_click=on_open_existing_market),
        Cancel(Const("Close")),
        state=AddMarketSG.market_exists,
    ),
    on_start=on_dialog_start,
)
