from datetime import datetime, timedelta, timezone

import aiohttp
from pydantic import BaseModel

from .scoring import SCORING_NODE_URL

REFERENCE_NODE_URL = "https://api2.aleph.im".rstrip("/")
RECENT_METRICS_API_URL = (
    "/api/v0/messages.json?addresses=0x4D52380D3191274a04846c89c069E6C3F2Ed94e4"
)


class MetricsAge(BaseModel):
    acceptable: bool
    scoring_node: float
    reference_node: float


def filter_metrics_messages(messages: list[dict]) -> list[dict]:
    """
    Filter out messages that are not metrics. Scoring messages are expected to be mixed.
    """
    return [
        message
        for message in messages
        if message["content"]["type"] == "aleph-network-metrics"
    ]


async def get_recent_metrics(api_url: str) -> list[dict]:
    """
    Get the most recent metrics from the `pyaleph` node used for scoring.
    """
    session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))
    async with session:
        print(session)
        async with session.get(api_url + RECENT_METRICS_API_URL) as response:
            response.raise_for_status()
            messages = await response.json()
    return filter_metrics_messages(messages["messages"])


async def get_recent_metrics_age(api_url_prefix: str, now: datetime) -> timedelta:
    """
    Get the age of the most recent metrics from the specified `pyaleph` node.
    """
    recent_metrics = await get_recent_metrics(api_url_prefix)
    signed_timestamp: float = recent_metrics[0]["content"]["time"]
    signed_datetime = datetime.fromtimestamp(signed_timestamp, tz=timezone.utc)
    return now - signed_datetime


async def get_metrics_age_by_node() -> MetricsAge:
    now = datetime.now(timezone.utc)
    scoring_node_age: timedelta = await get_recent_metrics_age(SCORING_NODE_URL, now)
    reference_node_age: timedelta = await get_recent_metrics_age(
        REFERENCE_NODE_URL, now
    )

    acceptable_metrics_age = timedelta(
        minutes=90
    )  # Metrics should be published every hour

    return MetricsAge(
        acceptable=scoring_node_age < acceptable_metrics_age
        and reference_node_age < acceptable_metrics_age,
        scoring_node=scoring_node_age.total_seconds(),
        reference_node=reference_node_age.total_seconds(),
    )
