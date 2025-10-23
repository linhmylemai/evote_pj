from fastapi import APIRouter
router = APIRouter()
@router.post("/cast")
def cast_vote():
    return {"message": "Endpoint Cast"}