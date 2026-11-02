import logging as lg

import fastapi as fa

import config.config as cn
import database.database as db
from routers.optimize import optimize_router
from routers.performance import performance_router
from routers.score import score_router

lg.basicConfig(
    level=lg.DEBUG,
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
log = lg.getLogger(__name__)

if __name__ == "__main__":
    log.info("main is a server and should not be run as main")

else:
    log.info("Starting backend")
    db.make_database()
    cn.make_scoring()
    log.info("Database ready")
    app = fa.FastAPI()
    app.include_router(performance_router)
    app.include_router(score_router)
    app.include_router(optimize_router)
    log.info("Server started")
