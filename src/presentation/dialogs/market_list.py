import operator
from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, Cancel, ScrollingGroup, Select, SwitchTo, Back, Row, Group, Url
from aiogram_dialog.widgets.text import Const, Format
from fluentogram import TranslatorRunner

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
    i18n: TranslatorRunner = dialog_manager.middleware_data["i18n"]
    user_id = dialog_manager.event.from_user.id
    markets = await list_use_case(user_id)
    return {
        "markets": markets,
        "text_title": i18n.market_list_title(),
        "text_empty": i18n.market_list_empty(),
        "text_close": i18n.common_close()
    }


async def get_selected_market(dialog_manager: DialogManager, **kwargs):
    get_use_case: GetMarketUseCase = dialog_manager.middleware_data["get_market_use_case"]
    i18n: TranslatorRunner = dialog_manager.middleware_data["i18n"]
    market_id = dialog_manager.dialog_data.get("selected_market_id")
    if not market_id:
        return {}
    market = await get_use_case(market_id)
    if not market:
        return {}
        
    status_icon = "✅" if market.is_active else "⏸️"
    status_text = i18n.market_list_status_active() if market.is_active else i18n.market_list_status_paused()
    
    toggle_text = i18n.market_list_toggle_pause() if market.is_active else i18n.market_list_toggle_resume()
    
    return {
        "market": market,
        "text_info": i18n.market_view_info(
            title=market.title,
            icon=status_icon,
            status=status_text,
            price=market.target_price
        ),
        "status_icon": status_icon,
        "status_text": status_text,
        "toggle_text": toggle_text,
        "text_open_polymarket": i18n.market_view_open_polymarket(),
        "text_edit_price": i18n.market_view_edit_price(),
        "text_delete": i18n.market_view_delete(),
        "text_back": i18n.common_back()
    }


async def get_edit_price_strings(dialog_manager: DialogManager, **kwargs):
    i18n: TranslatorRunner = dialog_manager.middleware_data["i18n"]
    return {
        "text_edit_prompt": i18n.market_edit_price_prompt(),
        "text_back": i18n.common_back()
    }


async def on_market_selected(c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    manager.dialog_data["selected_market_id"] = int(item_id)
    await manager.switch_to(MarketListSG.view_market)


async def on_price_updated(c: CallbackQuery, widget: Any, manager: DialogManager, item_id: str):
    price = int(item_id)
    await _update_market_price(manager, price)


async def on_manual_price_update(message: Message, widget: MessageInput, manager: DialogManager):
    i18n: TranslatorRunner = manager.middleware_data["i18n"]
    try:
        price = int(message.text)
        await _update_market_price(manager, price)
    except ValueError:
        await message.answer(i18n.err_invalid_number())


async def _update_market_price(manager: DialogManager, price: int):
    update_use_case: UpdateMarketUseCase = manager.middleware_data["update_market_use_case"]
    i18n: TranslatorRunner = manager.middleware_data["i18n"]
    market_id = manager.dialog_data["selected_market_id"]
    
    # Exceptions will bubble up to the global error handler
    await update_use_case(market_id=market_id, new_target_price=price)
    # Return to view_market to see updated info
    await manager.switch_to(MarketListSG.view_market)
    await manager.event.answer(i18n.market_updated_success())


async def on_delete_market(c: CallbackQuery, widget: Any, manager: DialogManager):
    delete_use_case: DeleteMarketUseCase = manager.middleware_data["delete_market_use_case"]
    i18n: TranslatorRunner = manager.middleware_data["i18n"]
    market_id = manager.dialog_data["selected_market_id"]
    
    # Exceptions will bubble up to the global error handler
    await delete_use_case(market_id=market_id)
    await manager.switch_to(MarketListSG.list)
    await c.answer(i18n.market_deleted(), show_alert=True)


async def on_toggle_monitoring(c: CallbackQuery, widget: Any, manager: DialogManager):
    toggle_use_case: ToggleMonitoringUseCase = manager.middleware_data["toggle_monitoring_use_case"]
    get_use_case: GetMarketUseCase = manager.middleware_data["get_market_use_case"]
    i18n: TranslatorRunner = manager.middleware_data["i18n"]
    market_id = manager.dialog_data["selected_market_id"]
    
    market = await get_use_case(market_id)
    if not market:
        return

    new_status = not market.is_active
    await toggle_use_case(market_id=market_id, is_active=new_status)
    
    status_msg = i18n.market_monitoring_resumed() if new_status else i18n.market_monitoring_paused()
    await c.answer(status_msg, show_alert=False)
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
        Format("{text_title}"),
        Format("{text_empty}", when=lambda d, *k: not d.get("markets")),
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
        Cancel(Format("{text_close}")),
        state=MarketListSG.list,
        getter=get_markets,
    ),
    Window(
        Format("{text_info}"),
        Url(
            Format("{text_open_polymarket}"),
            Format("{market.url}"),
        ),
        Row(
            SwitchTo(Format("{text_edit_price}"), id="edit_price_btn", state=MarketListSG.edit_price),
            Button(Format("{toggle_text}"), id="toggle_mon_btn", on_click=on_toggle_monitoring),
        ),
        Button(Format("{text_delete}"), id="delete_market", on_click=on_delete_market),
        Back(Format("{text_back}")),
        state=MarketListSG.view_market,
        getter=get_selected_market,
    ),
    Window(
        Format("{text_edit_prompt}"),
        Group(
            get_price_buttons_edit(),
            width=4,
        ),
        MessageInput(on_manual_price_update),
        Back(Format("{text_back}")),
        state=MarketListSG.edit_price,
        getter=get_edit_price_strings,
    ),
    on_start=on_dialog_start,
)
