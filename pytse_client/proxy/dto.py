from dataclasses import dataclass


@dataclass
class ShareholderData:
    id: str
    name: str
    instrument_id: str  # it's cIsin key in response
    shares: float
    percentage: float
    change: float
