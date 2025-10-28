from fastapi import FastAPI
from .api import user_routes as users, candidate_routes as candidates, office_routes as offices, vote_routes as votes, result_routes as results, config_route as config
from .api.auth import reset_password as reset, change_password as change, login, logout
from .domain import user as models
from .core.database import engine
from .core import database
from .core.init_super_admin import init_super_admin
from fastapi.middleware.cors import CORSMiddleware


models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    # title="Voting API",
    # docs_url="/docs",  # explicitly set docs URL
    # openapi_url="/openapi.json",  # explicitly set OpenAPI URL
    # root_path="/api"  # set the root path
    title="Python Voting API",
    docs_url="/docs",
    openapi_url="/openapi.json",
    root_path="/api",
)




origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
def root():
    return {
        "message": "Welcome to Voting API",
        "version": "1.0",
        "docs_url": "/docs",
        "status": "running"
    }


@app.get("/app")
def app_status():
    return {"message": "API is running"}


@app.on_event("startup")
def create_super_admin():
    db = database.SessionLocal()
    init_super_admin(db)
    db.close()



app.include_router(users.router)
app.include_router(change.router)
app.include_router(reset.router)
app.include_router(login.router)
app.include_router(logout.router)
app.include_router(candidates.router)
app.include_router(offices.router)
app.include_router(votes.router)
app.include_router(results.router)
app.include_router(config.router)
