from fastapi import APIRouter
from src.api.v1 import contacts, users, auth
from src.api.v1 import utils

router = APIRouter()

router.include_router(contacts.router, prefix="/v1")
router.include_router(users.router, prefix="/v1")
router.include_router(auth.router, prefix="/v1")

router.include_router(utils.router, prefix="/v1")




