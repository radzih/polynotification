from aiogram.fsm.state import State, StatesGroup


class AddMarketSG(StatesGroup):
    waiting_for_url = State()
    selecting_market = State()
    selecting_price = State()
    market_exists = State()
    success = State()


class MarketListSG(StatesGroup):
    list = State()
    view_market = State()
    edit_price = State()
