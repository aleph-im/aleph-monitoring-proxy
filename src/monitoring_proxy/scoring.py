import aiohttp
from pydantic import BaseModel

SCORING_NODE_URL = "http://51.159.106.166:4024".rstrip("/")


class ScoringNodeSyncStatus(BaseModel):
    acceptable: bool
    pending_messages: float
    pending_txs: float
    eth_height_remaining: float


def parse_prometheus_metrics(metrics: str) -> dict[str, float]:
    """
    Parse Prometheus metrics into a dictionary.
    """
    parsed_metrics = {}
    for line in metrics.splitlines():
        if not line.startswith("#"):
            print([line])
            key, value = line.split(" ")
            parsed_metrics[key] = float(value)
    return parsed_metrics


async def get_scoring_node_metrics() -> dict[str, float]:
    """
    Download and parse the Prometheus metrics from the `pyaleph` node
    used for scoring.
    """
    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=10)
    ) as session:
        async with session.get(f"{SCORING_NODE_URL}/metrics") as response:
            response.raise_for_status()
            metrics = await response.text()
    return parse_prometheus_metrics(metrics)


async def get_node_sync_status() -> ScoringNodeSyncStatus:
    """
    Check that the `pyaleph` node used for scoring is in sync.
    """
    scoring_node_metrics = await get_scoring_node_metrics()

    pending_messages: float = scoring_node_metrics[
        "pyaleph_status_sync_pending_messages_total"
    ]
    pending_txs: float = scoring_node_metrics["pyaleph_status_sync_pending_txs_total"]
    eth_height_remaining: float = scoring_node_metrics[
        "pyaleph_status_chain_eth_height_remaining_total"
    ]

    return ScoringNodeSyncStatus(
        acceptable=pending_messages < 50
        and pending_txs < 5
        and eth_height_remaining < 1000,
        pending_messages=pending_messages,
        pending_txs=pending_txs,
        eth_height_remaining=eth_height_remaining,
    )
