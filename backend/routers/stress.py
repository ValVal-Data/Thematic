import fastapi as fa

stress_router=fa.APIRouter(prefix="/stress")

@stress_router.get("/")
def get_position():
    return 0