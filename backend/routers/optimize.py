import logging as lg
from concurrent.futures import ProcessPoolExecutor

import fastapi as fa

import services.optimize_service as ser

optimize_router = fa.APIRouter(prefix="/optimize")

log = lg.getLogger(__name__)

executor = ProcessPoolExecutor()


@optimize_router.get("/progress", summary="Get progress")
def get_progress(job_id: str) -> dict:
    """Get progress for a certain job id"""
    return ser.get_progress(job_id)


@optimize_router.post("/optimize", summary="Optimize")
def post_optimize(cons: dict) -> dict:
    """Start new optimization process"""
    job_id = ser.new_job(cons)
    future = executor.submit(ser.post_optimize, cons["cons"], job_id)
    ser.set_future(future, job_id)
    return {"job_id": job_id}
