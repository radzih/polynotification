class ApplicationException(Exception):
    """Base class for all application exceptions."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class InvalidMarketUrlError(ApplicationException):
    """Raised when the provided market URL is invalid."""
    def __init__(self):
        super().__init__("The provided Polymarket URL is invalid. Please make sure it's a correct event URL.")


class InvalidTargetPriceError(ApplicationException):
    """Raised when the target price is not between 0 and 100."""
    def __init__(self):
        super().__init__("Target price must be between 0 and 100.")


class MarketNotFoundError(ApplicationException):
    """Raised when the market cannot be found in the database or API."""
    def __init__(self, market_id: str | int):
        super().__init__(f"Market with ID {market_id} not found.")


class MarketAlreadyExistsError(ApplicationException):
    """Raised when the market is already tracked by the user."""
    def __init__(self, market_id: int):
        self.market_id = market_id
        super().__init__("You are already tracking this market.")


class MarketApiError(ApplicationException):
    """Raised when there is an error fetching data from Polymarket API."""
    def __init__(self, message: str):
        super().__init__(f"Polymarket API error: {message}")


class TokenIdNotFoundError(ApplicationException):
    """Raised when the token ID for the 'Yes' outcome cannot be found."""
    def __init__(self, market_id: str):
        super().__init__(f"Could not find 'Yes' outcome token ID for market {market_id}.")
