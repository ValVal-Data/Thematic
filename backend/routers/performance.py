import fastapi as fa

import services.performance_service as ser

performance_router = fa.APIRouter(prefix="/performance")


@performance_router.get("/perf")
def get_perf(job_id) -> dict:
    return ser.get_perf(job_id)
