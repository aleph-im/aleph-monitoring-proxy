from pathlib import Path

from fastapi import FastAPI, Response, status
from fastapi.responses import HTMLResponse

from monitoring_proxy.metrics import MetricsAge, get_metrics_age_by_node
from monitoring_proxy.scoring import ScoringNodeSyncStatus, get_node_sync_status

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    # dynamically list fastapi endpoints
    #
    endpoints = []
    for route in app.routes:
        if hasattr(route, "path"):
            endpoints.append(route.path)
    return (Path(__file__).parent / "templates/index.html").read_text()


@app.get("/check/scoring/node_sync")
async def check_scoring_node_sync(response: Response) -> ScoringNodeSyncStatus:
    """
    Check that the `pyaleph` node used for scoring is in sync.

    Returns the status code 503 if the node is not in sync.
    """
    node_status = await get_node_sync_status()
    response.status_code = (
        status.HTTP_201_CREATED
        if node_status.acceptable
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return node_status


@app.get("/check/metrics/age")
async def check_metrics_age(response: Response) -> MetricsAge:
    """
    Check that the most recent metrics have been published on `pyaleph` nodes.
    """
    metrics_age = await get_metrics_age_by_node()
    response.status_code = (
        status.HTTP_201_CREATED
        if metrics_age.acceptable
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )
    return metrics_age
