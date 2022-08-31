from dataclasses import dataclass


@dataclass
class ShareholderData:
    id: str
    name: str
    instrument_id: str  # it's cIsin key in response
    shares: float
    percentage: float
    change: float


@dataclass
class InstrumentHistoryResponse:
    """
    Represent the response coming from InstrumentHistory API
    """

    total_shares: int
    base_volume: int
