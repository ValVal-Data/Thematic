import fastapi as fa

import services.score_service as ser

score_router = fa.APIRouter(prefix="/score")


@score_router.get("/score", summary="Get score")
def get_score() -> dict:
    """Return score for whole universe"""
    return ser.get_score("database/database.db")


@score_router.get("/universe", summary="Get universe")
def get_universe() -> dict:
    """Return whole universe"""
    return ser.get_universe("database/database.db")


@score_router.get("/weight", summary="Get weights")
def get_weight() -> dict:
    """Return scoring weights"""
    return ser.get_weight("config/weight.json")


@score_router.post("/score", summary="Calculate thematic score")
def calc_score() -> None:
    """Calculate thematic score"""
    ser.calc_score()


@score_router.put("/weight", summary="Update weight")
def update_weight(data: dict) -> dict:
    """Update weight with new ones"""
    ser.update_weight("config/weight.json", data)
    return {"weight": data}


@score_router.put("/universe", summary="Update universe")
def update_universe(data: dict) -> dict:
    """Update universe database"""
    ser.update_universe("database/database.db", data)
    return {"universe": data}
