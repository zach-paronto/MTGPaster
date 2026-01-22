from dataclasses import dataclass


@dataclass
class ApiError:
    message: str = ""
    http_code: int = 500