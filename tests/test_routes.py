from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from monitoring_proxy import app
from monitoring_proxy.metrics import MetricsAge
from monitoring_proxy.scoring import ScoringNodeSyncStatus

client = TestClient(app)

def test_index():
    response = client.get("/")
    assert response.status_code == 200
    assert "<h1>" in response.text


@pytest.mark.asyncio
async def test_returns_201_when_node_sync_is_acceptable():
    async_mock = AsyncMock()
    async_mock.return_value = ScoringNodeSyncStatus(
        acceptable=True, pending_messages=10, pending_txs=2, eth_height_remaining=500
    )

    with patch("monitoring_proxy.main.get_node_sync_status", new=async_mock):
        response = client.get("/check/scoring/node_sync")

    assert response.status_code == 201
    assert response.json() == {
        "acceptable": True,
        "pending_messages": 10,
        "pending_txs": 2,
        "eth_height_remaining": 500,
    }

@pytest.mark.asyncio
async def test_returns_503_when_node_sync_is_not_acceptable():
    async_mock = AsyncMock()
    async_mock.return_value = ScoringNodeSyncStatus(
        acceptable=False, pending_messages=100, pending_txs=10, eth_height_remaining=2000
    )

    with patch("monitoring_proxy.main.get_node_sync_status", new=async_mock):
        response = client.get("/check/scoring/node_sync")

    assert response.status_code == 503
    assert response.json() == {
        "acceptable": False,
        "pending_messages": 100,
        "pending_txs": 10,
        "eth_height_remaining": 2000,
    }

@pytest.mark.asyncio
async def test_returns_201_when_metrics_age_is_acceptable():
    async_mock = AsyncMock()
    async_mock.return_value = MetricsAge(
        acceptable=True, scoring_node=3000, reference_node=3000
    )

    with patch("monitoring_proxy.main.get_metrics_age_by_node", new=async_mock):
        response = client.get("/check/metrics/age")

    assert response.status_code == 201
    assert response.json() == {
        "acceptable": True,
        "scoring_node": 3000,
        "reference_node": 3000,
    }

@pytest.mark.asyncio
async def test_returns_503_when_metrics_age_is_not_acceptable():
    async_mock = AsyncMock()
    async_mock.return_value = MetricsAge(
        acceptable=False, scoring_node=6000, reference_node=6000
    )

    with patch("monitoring_proxy.main.get_metrics_age_by_node", new=async_mock):
        response = client.get("/check/metrics/age")

    assert response.status_code == 503
    assert response.json() == {
        "acceptable": False,
        "scoring_node": 6000,
        "reference_node": 6000,
    }