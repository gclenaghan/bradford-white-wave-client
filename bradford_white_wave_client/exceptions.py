class BradfordWhiteError(Exception):
    """Base exception for Bradford White Wave Client."""
    pass

class BradfordWhiteAuthError(BradfordWhiteError):
    """Raised when authentication fails."""
    pass

class BradfordWhiteConnectError(BradfordWhiteError):
    """Raised when connection or API request fails."""
    pass
