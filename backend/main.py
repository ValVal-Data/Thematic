import database.database as db
import config.config as cn
import logging as lg
import fastapi as fa
from routers.stress import stress_router
from routers.score import score_router
from routers.optimize import optimize_router

lg.basicConfig(
    level=lg.DEBUG,
    format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
log=lg.getLogger(__name__)

if __name__ == "__main__":
    log.info("main is a server and should not be run as main")

else:
    log.info("Starting backend")
    db.make_database()
    cn.make_scoring()
    log.info("Database ready")
    app = fa.FastAPI()
    app.include_router(stress_router)
    app.include_router(score_router)
    app.include_router(optimize_router)
    log.info("Server started")