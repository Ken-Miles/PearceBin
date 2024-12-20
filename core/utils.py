"""PearceBin (from Mystbin). Share code easily.

Copyright (C) 2020-Current PythonistaGuild
Forked and Minor changes made by Aiden Pearce

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from __future__ import annotations

import base64
import binascii
import datetime
import json
import re
import secrets
from typing import Any

import starlette_plus

from core import CONFIG


TOKEN_REGEX = re.compile(r"[a-zA-Z0-9_-]{23,28}\.[a-zA-Z0-9_-]{6,7}\.[a-zA-Z0-9_-]{27,}")


def generate_id() -> str:
    return secrets.token_hex(9)


def generate_safety_token() -> str:
    return secrets.token_urlsafe(64)


async def json_or_text(request: starlette_plus.Request) -> dict[str, Any] | str:
    text: str = str(await request.body())

    try:
        data: dict[str, Any] = json.loads(text)
    except json.JSONDecodeError:
        return text

    return data


def validate_paste(data: dict[str, Any]) -> starlette_plus.Response | None:
    limit: int = CONFIG["PASTES"]["char_limit"]
    file_limit: int = CONFIG["PASTES"]["file_limit"]

    try:
        files: list[dict[str, str | None]] = data["files"]
    except KeyError:
        return starlette_plus.JSONResponse({"error": 'Missing the "files" parameter.'}, status_code=400)

    if len(files) > file_limit:
        return starlette_plus.JSONResponse(
            {"error": f'Paste exceeds the file limit of "{file_limit}" files.'},
            status_code=400,
        )

    for index, file in enumerate(files):
        try:
            content: str | None = file["content"]
        except KeyError:
            return starlette_plus.JSONResponse(
                {"error": f'The file at index "{index}" is missing the content parameter.'},
                status_code=400,
            )

        if not content:
            return starlette_plus.JSONResponse(
                {"error": f'The file at index "{index}" has no content.'},
                status_code=400,
            )

        if len(content) > limit:
            return starlette_plus.JSONResponse(
                {"error": f'The file at index "{index}" exceeds content size limits of "{limit}" characters.'},
                status_code=400,
            )


def validate_discord_token(token: str) -> bool:
    try:
        # Just check if the first part validates as a user ID
        (user_id, _, _) = token.split(".")
        user_id = int(base64.b64decode(user_id + "==", validate=True))
    except (ValueError, binascii.Error):
        return False
    else:
        return True


def pluralize(count: int, singular: str) -> str:
    return singular if count == 1 else singular + "s"


def natural_time(
    td: datetime.timedelta,
    /,
    *,
    source: datetime.datetime | None = None,
) -> str:
    now = source or datetime.datetime.now(datetime.UTC)

    then = now - td
    future = then > now

    seconds = round(td.total_seconds())

    if seconds < 60 and not future:
        return "now"

    ago = "{delta} from now" if future else "{delta} ago"

    years, seconds = divmod(seconds, 60 * 60 * 24 * 365)
    months, seconds = divmod(seconds, 60 * 60 * 24 * 30)
    weeks, seconds = divmod(seconds, 60 * 60 * 24 * 7)
    days, seconds = divmod(seconds, 60 * 60 * 24)
    hours, seconds = divmod(seconds, 60 * 60)
    minutes, seconds = divmod(seconds, 60)

    ret = ""

    if years:
        ret += f"{years} {pluralize(years, 'year')}"
        if months:
            ret += f", {months} {pluralize(months, 'month')}"
    elif months:
        ret += f"{months} {pluralize(months, 'month')}"
    elif weeks:
        ret += f"{weeks} {pluralize(weeks, 'week')}"
        if days:
            ret += f", {days} {pluralize(days, 'day')}"
    elif days:
        ret += f"{days} {pluralize(days, 'day')}"

    if hours and not years and not months and not weeks and not days:
        if ret:
            ret += ", "
        ret += f"{hours} {pluralize(hours, 'hour')}"
    if minutes and not years and not months and not weeks and not days and not hours:
        if ret:
            ret += ", "
        ret += f"{minutes} {pluralize(minutes, 'minute')}"

    formatted_ret = ", ".join(ret.split(", ")[:2])

    return ago.format(delta=formatted_ret)
