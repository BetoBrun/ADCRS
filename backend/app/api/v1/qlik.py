from fastapi import APIRouter
router = APIRouter()

@router.get("/")
async def placeholder():
    return {"status": "not_implemented", "endpoint": "qlik"}
