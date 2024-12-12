from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from aioresponses import aioresponses

from monitoring_proxy.metrics import (
    filter_metrics_messages,
    get_metrics_age_by_node,
    get_recent_metrics,
    get_recent_metrics_age,
)


@pytest.mark.asyncio
async def test_returns_filtered_metrics():
    messages = [
        {"content": {"type": "aleph-network-metrics"}},
        {"content": {"type": "other-type"}},
    ]
    filtered = filter_metrics_messages(messages)
    assert len(filtered) == 1
    assert filtered[0]["content"]["type"] == "aleph-network-metrics"


@pytest.mark.asyncio
async def test_returns_recent_metrics():
    with aioresponses() as m:
        m.get(
            "http://example.com/api/v0/messages.json?addresses=0x4D52380D3191274a04846c89c069E6C3F2Ed94e4",
            payload={
                "messages": [
                    {
                        "content": {
                            "type": "aleph-network-metrics",
                            "time": 1734010566.887175,
                        }
                    },
                    {
                        "content": {
                            "type": "aleph-network-metrics",
                            "time": 1734010555.000000,
                        }
                    },
                ]
            },
        )

        metrics = await get_recent_metrics("http://example.com")

    assert len(metrics) == 2
    assert metrics[0]["content"]["type"] == "aleph-network-metrics"


@pytest.mark.asyncio
async def test_returns_recent_metrics_age():
    now = datetime.fromtimestamp(1734010566.887175, tz=timezone.utc)
    async_mock = AsyncMock()
    async_mock.return_value = [
        {"content": {"type": "aleph-network-metrics", "time": now.timestamp()}}
    ]

    with patch("monitoring_proxy.metrics.get_recent_metrics", new=async_mock):
        age = await get_recent_metrics_age("https://example.com", now)

    assert age < timedelta(minutes=90)


@pytest.mark.asyncio
async def test_returns_metrics_age_by_node():
    now = datetime.fromtimestamp(1734010566.887175, tz=timezone.utc)
    async_mock = AsyncMock()
    async_mock.return_value = [
        {"content": {"time": (now - timedelta(minutes=30)).timestamp()}}
    ]

    with patch("monitoring_proxy.metrics.get_recent_metrics", new=async_mock):
        metrics_age = await get_metrics_age_by_node()

    assert metrics_age.acceptable
    assert metrics_age.scoring_node < 5400
    assert metrics_age.reference_node < 5400
