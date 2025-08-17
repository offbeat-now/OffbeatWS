# app/main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes import auth, user, organization as org, accommodation, job, application, social, enum
# , users, hosts, accommodations, jobs, bookings, reviews, forums, messages
from app.core.config import get_settings

settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Offbeat",
    version="0.1.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Add CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["https://offbeat.tours/",
#                    "https://offbeat.tours",
#                    "https://www.offbeat.tours/",
#                    "https://www.offbeat.tours"], 
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# Add session middleware for OAuth flows
# app.add_middleware(
#     SessionMiddleware,
#     secret_key=settings.secret_key
# )

# Include API routes

# ENUMS

app.include_router(enum.router, prefix=f"{settings.api_prefix}/enum", tags=["Enums"])


# AUTH & PROFILE
app.include_router(auth.router, prefix=f"{settings.api_prefix}/auth", tags=["Authentication"])
app.include_router(user.router, prefix=f"{settings.api_prefix}/user", tags=["Users"])
app.include_router(org.router, prefix=f"{settings.api_prefix}/org", tags=["Organizations"])


# CORE
app.include_router(accommodation.router, prefix=f"{settings.api_prefix}/acc", tags=["Accommodations"])
app.include_router(job.router, prefix=f"{settings.api_prefix}/job", tags=["Jobs"])
app.include_router(application.router, prefix=f"{settings.api_prefix}/application", tags=["Applications"])
# app.include_router(bookings.router, prefix=f"{settings.api_prefix}/bookings", tags=["Bookings"])


# SOCIALS

app.include_router(social.router, prefix=f"{settings.api_prefix}/social", tags=["Socials"])

# BLOGS

# PACKAGES

@app.get("/")
async def root():
    return {"message": "Welcome to the Offbeat API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Run with: uvicorn app.main:app --reload