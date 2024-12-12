from unittest.mock import AsyncMock, patch

import pytest
from aiohttp.client_exceptions import ClientError
from aioresponses import aioresponses

from monitoring_proxy.scoring import (
    get_node_sync_status,
    get_scoring_node_metrics,
    parse_prometheus_metrics,
)

NODE_METRICS = "\n".join(
    (
        "pyaleph_status_sync_pending_messages_total 10",
        "pyaleph_status_sync_pending_txs_total 2",
        "pyaleph_status_chain_eth_height_remaining_total 500",
    )
)


@pytest.mark.asyncio
async def test_parse_prometheus_metrics():
    metrics = parse_prometheus_metrics(NODE_METRICS)
    assert metrics == {
        "pyaleph_status_sync_pending_messages_total": 10,
        "pyaleph_status_sync_pending_txs_total": 2,
        "pyaleph_status_chain_eth_height_remaining_total": 500,
    }


@pytest.mark.asyncio
async def test_returns_scoring_node_metrics():
    with aioresponses() as mock_responses:
        mock_responses.get("http://51.159.106.166:4024/metrics", body=NODE_METRICS)

        metrics = await get_scoring_node_metrics()
        assert metrics["pyaleph_status_sync_pending_messages_total"] == 10
        assert metrics["pyaleph_status_sync_pending_txs_total"] == 2
        assert metrics["pyaleph_status_chain_eth_height_remaining_total"] == 500


@pytest.mark.asyncio
async def test_returns_node_sync_status():
    async_mock = AsyncMock()
    async_mock.return_value = {
        "pyaleph_status_sync_pending_messages_total": 10,
        "pyaleph_status_sync_pending_txs_total": 2,
        "pyaleph_status_chain_eth_height_remaining_total": 500,
    }

    with patch("monitoring_proxy.scoring.get_scoring_node_metrics", new=async_mock):
        status = await get_node_sync_status()
        assert status.acceptable
        assert status.pending_messages == 10
        assert status.pending_txs == 2
        assert status.eth_height_remaining == 500


@pytest.mark.asyncio
async def test_handles_high_pending_messages():
    async_mock = AsyncMock()
    async_mock.return_value = {
        "pyaleph_status_sync_pending_messages_total": 1000,
        "pyaleph_status_sync_pending_txs_total": 0,
        "pyaleph_status_chain_eth_height_remaining_total": 0,
    }

    with patch("monitoring_proxy.scoring.get_scoring_node_metrics", new=async_mock):
        status = await get_node_sync_status()
        assert not status.acceptable


@pytest.mark.asyncio
async def test_handles_high_pending_txs():
    async_mock = AsyncMock()
    async_mock.return_value = {
        "pyaleph_status_sync_pending_messages_total": 0,
        "pyaleph_status_sync_pending_txs_total": 10,
        "pyaleph_status_chain_eth_height_remaining_total": 0,
    }

    with patch("monitoring_proxy.scoring.get_scoring_node_metrics", new=async_mock):
        status = await get_node_sync_status()
        assert not status.acceptable


@pytest.mark.asyncio
async def test_handles_high_eth_height_remaining():
    async_mock = AsyncMock()
    async_mock.return_value = {
        "pyaleph_status_sync_pending_messages_total": 0,
        "pyaleph_status_sync_pending_txs_total": 0,
        "pyaleph_status_chain_eth_height_remaining_total": 5000,
    }

    with patch("monitoring_proxy.scoring.get_scoring_node_metrics", new=async_mock):
        status = await get_node_sync_status()
        assert not status.acceptable


@pytest.mark.asyncio
async def test_handles_client_error():
    with aioresponses() as mock_responses:
        mock_responses.get("http://51.159.106.166:4024/metrics", exception=ClientError)

        with pytest.raises(ClientError):
            await get_scoring_node_metrics()
