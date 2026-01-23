class HyperLiquidError(Exception):
    """Base exception for HyperLiquid API errors."""

    pass


class ClientError(HyperLiquidError):
    """HTTP 4xx errors from the HyperLiquid API."""

    def __init__(
        self,
        status_code: int,
        error_code: str | None,
        error_message: str | None,
        headers: dict | None = None,
        error_data: dict | None = None,
    ):
        self.status_code = status_code
        self.error_code = error_code
        self.error_message = error_message
        self.headers = headers
        self.error_data = error_data
        super().__init__(f"ClientError {status_code}: {error_message}")

    def __repr__(self) -> str:
        return (
            f"ClientError(status_code={self.status_code}, "
            f"error_code={self.error_code}, error_message={self.error_message})"
        )


class ServerError(HyperLiquidError):
    """HTTP 5xx errors from the HyperLiquid API."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"ServerError {status_code}: {message}")

    def __repr__(self) -> str:
        return f"ServerError(status_code={self.status_code}, message={self.message})"
