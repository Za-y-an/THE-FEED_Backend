# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import all routers
from auth.router import router as auth_router
from posts.router import router as posts_router
from users.router import router as users_router

app = FastAPI(title="THE FEED API")

# Add CORS Middleware so Flutter can communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local development
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers (including Authorization/Bearer tokens)
)

# Register the routes
app.include_router(auth_router)
app.include_router(posts_router)
app.include_router(users_router)

@app.get("/")
async def root():
    return {"message": "THE FEED API is online and fully operational."}