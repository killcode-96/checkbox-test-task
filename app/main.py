from fastapi import FastAPI

from app.api import users, receipts, public


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Checkbox Test Task"}


app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(receipts.router, prefix="/receipts", tags=["receipts"])
app.include_router(public.router, prefix="/public", tags=["public"])
