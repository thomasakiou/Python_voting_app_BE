from fastapi import FastAPI
from .api import user_routes as users, candidate_routes as candidates, office_routes as offices, vote_routes as votes, result_routes as results, config_route as config, voting_time_routes as voting_time
from .api.auth import otp_login, admin_login, logout
from .domain import user as models
from .domain import otp as otp_models  # ensures otps table is created
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




# origins = ["*"]
origins = [
    "https://votingappfe.netlify.app", "http://localhost:3000", "https://onlinevoter.netlify.app"
    # "http://localhost:8000" 
]

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
app.include_router(otp_login.router)    # POST /login  &  POST /verify-otp  (voters)
app.include_router(admin_login.router)  # POST /admin/login                  (admin/super-admin)
app.include_router(logout.router)
app.include_router(candidates.router)
app.include_router(offices.router)
app.include_router(votes.router)
app.include_router(results.router)
app.include_router(config.router)
app.include_router(voting_time.router)
