import operator
from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Cancel, ScrollingGroup, Select, SwitchTo, Back, Row, Group, Url
from aiogram_dialog.widgets.text import Const, Format

from src.domain.entities.market import MarketDTO
from src.presentation.states import MarketListSG
from src.use_cases.market.list import ListUserMarketsUseCase
from src.use_cases.market.update import UpdateMarketUseCase
from src.use_cases.market.delete import DeleteMarketUseCase
from src.use_cases.market.get import GetMarketUseCase
from src.use_cases.market.toggle_monitoring import ToggleMonitoringUseCase


async def on_dialog_start(start_data: dict, manager: DialogManager):
    if start_data and "selected_market_id" in start_data:
        manager.dialog_data["selected_market_id"] = start_data["selected_market_id"]


async def get_markets(dialog_manager: DialogManager, **kwargs):
    list_use_case: ListUserMarketsUseCase = dialog_manager.middleware_data["list_markets_use_case"]
    user_id = dialog_manager.event.from_user.id
    markets = await list_use_case(user_id)
    return {"markets": markets}


async def get_selected_market(dialog_manager: DialogManager, **kwargs):
    get_use_case: GetMarketUseCase = dialog_manager.middleware_data["get_market_use_case"]
    market_id = dialog_manager.dialog_data.get("selected_market_id")
    if not market_id:
        return {}
    market = await get_use_case(market_id)
    if not market:
        return {}
        
    status_icon = "✅" if market.is_active else "⏸️"
    status_text = "Active" if market.is_active else "Paused"
    
    toggle_text = "Pause Monitoring" if market.is_active else "Resume Monitoring"
    
    return {
        "market": market,
        "status_icon": status_icon,
        "status_text": status_text,
        "toggle_text": toggle_text
    }


async def on_market_selected(c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    manager.dialog_data["selected_market_id"] = int(item_id)
    await manager.switch_to(MarketListSG.view_market)


async def on_price_updated(c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    price = int(item_id)
    await _update_market_price(manager, price)


async def on_manual_price_update(message: Message, widget: MessageInput, manager: DialogManager):
    try:
        price = int(message.text)
        await _update_market_price(manager, price)
    except ValueError:
        await message.answer("Please enter a valid integer number.")


async def _update_market_price(manager: DialogManager, price: int):
    update_use_case: UpdateMarketUseCase = manager.middleware_data["update_market_use_case"]
    market_id = manager.dialog_data["selected_market_id"]
    
    # Exceptions will bubble up to the global error handler
    await update_use_case(market_id=market_id, new_target_price=price)
    # Return to view_market to see updated info
    await manager.switch_to(MarketListSG.view_market)
    await manager.event.answer("Market updated successfully!")


async def on_delete_market(c: CallbackQuery, widget: Any, manager: DialogManager):
    delete_use_case: DeleteMarketUseCase = manager.middleware_data["delete_market_use_case"]
    market_id = manager.dialog_data["selected_market_id"]
    
    # Exceptions will bubble up to the global error handler
    await delete_use_case(market_id=market_id)
    await manager.switch_to(MarketListSG.list)
    await c.answer("Market deleted.", show_alert=True)


async def on_toggle_monitoring(c: CallbackQuery, widget: Any, manager: DialogManager):
    toggle_use_case: ToggleMonitoringUseCase = manager.middleware_data["toggle_monitoring_use_case"]
    get_use_case: GetMarketUseCase = manager.middleware_data["get_market_use_case"]
    market_id = manager.dialog_data["selected_market_id"]
    
    market = await get_use_case(market_id)
    if not market:
        return

    new_status = not market.is_active
    await toggle_use_case(market_id=market_id, is_active=new_status)
    
    status_msg = "resumed" if new_status else "paused"
    await c.answer(f"Monitoring {status_msg}.", show_alert=False)
    # Force refresh of the window
    await manager.switch_to(MarketListSG.view_market)


def get_price_buttons_edit():
    # Generate buttons for 5, 10, ... 95
    prices = [(str(i), str(i)) for i in range(5, 100, 5)]
    return Select(
        Format("{item[0]}%"),
        id="price_select_edit",
        item_id_getter=operator.itemgetter(1),
        items=prices,
        on_click=on_price_updated,
    )


market_list_dialog = Dialog(
    Window(
        Const("<b>Your Monitored Markets</b>"),
        Const("No markets found.", when=lambda d, *k: not d.get("markets")),
        ScrollingGroup(
            Select(
                Format("{item.status_icon} {item.title}"),
                id="market_select",
                item_id_getter=lambda x: str(x.id),
                items="markets",
                on_click=on_market_selected,
            ),
            id="markets_group",
            width=1,
            height=10,
            hide_on_single_page=True,
        ),
        Cancel(Const("Close")),
        state=MarketListSG.list,
        getter=get_markets,
    ),
    Window(
        Format("<b>{market.title}</b>\n\n"
               "Status: {status_icon} {status_text}\n"
               "Target Price: {market.target_price}%"),
        Url(
            Const("Open on Polymarket"),
            Format("{market.url}"),
        ),
        Row(
            SwitchTo(Const("Edit Target Price"), id="edit_price_btn", state=MarketListSG.edit_price),
            Button(Format("{toggle_text}"), id="toggle_mon_btn", on_click=on_toggle_monitoring),
        ),
        Button(Const("Delete Market"), id="delete_market", on_click=on_delete_market),
        Back(Const("Back")),
        state=MarketListSG.view_market,
        getter=get_selected_market,
    ),
    Window(
        Const("Edit Market Target Price or enter manually"),
        Group(
            get_price_buttons_edit(),
            width=4,
        ),
        MessageInput(on_manual_price_update),
        Back(Const("Back")),
        state=MarketListSG.edit_price,
    ),
    on_start=on_dialog_start,
)
