"""Copyright(C) 2020 PythonistaGuild

This file is part of MystBin.

MystBin is free software: you can redistribute it and / or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

MystBin is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY
without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with MystBin.  If not, see <https://www.gnu.org/licenses/>.
"""
from typing import Union, Dict

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from models import Forbidden, Unauthorized, User, TokenResponse


router = APIRouter()
auth_model = HTTPBearer()


@router.get("/user", tags=["users"], response_model=User, responses={
    200: {"model": User},
    401: {"model": Unauthorized},
    403: {"model": Forbidden}},
    name="Get current user"
)
async def get_self(request: Request, authorization: str = Depends(auth_model)) -> Union[JSONResponse, Dict[str, Union[str, int, bool]]]:
    """ Gets the User object of the currently logged in user.
    * Requires authentication.
    """
    if not authorization:
        return JSONResponse({"error": "Forbidden"}, status_code=403)

    data = await request.app.state.db.get_user(token=authorization.credentials)
    if not data:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    return dict(data)

@router.post("/user/token-gen", tags=['users'], response_model=TokenResponse, responses={
    200: {"model": TokenResponse},
    401: {"model": Unauthorized},
    403: {"model": Forbidden}},
    name="Regenerate your token"
)
async def regen_token(request: Request, authorization: str = Depends(auth_model)) -> Union[JSONResponse, Dict[str, str]]:
    if not authorization:
        return JSONResponse({"error": "Forbidden"}, status_code=403)

    token = await request.app.state.db.regen_token(token=authorization.credentials)
    if not token:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    return {"token": token}
