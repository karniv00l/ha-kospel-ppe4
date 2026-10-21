"""Low-level client for the Kospel PPE4 MODBUS-over-HTTP API."""

from __future__ import annotations

import json
import re
from typing import Any

import aiohttp

from .const import DEFAULT_TIMEOUT

# The firmware emits invalid JSON for empty reads: `...,"res":}}`.
# Match the res payload (an object) if present, otherwise treat it as empty.
_RES_RE = re.compile(r'"res"\s*:\s*(\{.*\})\s*\}\s*$')
_STATUS_RE = re.compile(r'"status"\s*:\s*"([^"]*)"')


class KospelPPE4Error(Exception):
    """Base error talking to the heater."""


class KospelPPE4ConnectionError(KospelPPE4Error):
    """Could not reach the heater."""


class KospelPPE4ProtocolError(KospelPPE4Error):
    """The heater returned an unexpected / error response."""


class KospelPPE4Client:
    """Minimal async client for the PPE4 Wi-Fi module.

    The module exposes a MODBUS-style HTTP API with no authentication:

        GET  /api/<start>/<count>  -> read `count` 16-bit registers
        POST /api/write            -> write registers (see `write_registers`)
    """

    def __init__(
        self,
        host: str,
        session: aiohttp.ClientSession,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._host = host
        self._session = session
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    @property
    def host(self) -> str:
        return self._host

    def _url(self, path: str) -> str:
        return f"http://{self._host}/api/{path.lstrip('/')}"

    @staticmethod
    def _parse(text: str) -> dict[int, int]:
        """Parse a register read response into {address: value}.

        Tolerates the firmware's malformed empty payload (`"res":}}`).
        """
        status = _STATUS_RE.search(text)
        if status and status.group(1) != "OK":
            # e.g. "Wrong MODBUS start address." / "Wrong MODBUS register count."
            raise KospelPPE4ProtocolError(text.strip())

        m = _RES_RE.search(text.strip())
        if not m:
            return {}
        try:
            raw: dict[str, Any] = json.loads(m.group(1))
        except json.JSONDecodeError as err:
            raise KospelPPE4ProtocolError(f"bad res payload: {err}") from err
        return {int(k): int(v) for k, v in raw.items()}

    async def read_registers(self, start: int, count: int) -> dict[int, int]:
        """Read `count` consecutive registers starting at `start`."""
        url = self._url(f"{start}/{count}")
        try:
            async with self._session.get(url, timeout=self._timeout) as resp:
                resp.raise_for_status()
                text = await resp.text()
        except aiohttp.ClientError as err:
            raise KospelPPE4ConnectionError(str(err)) from err
        return self._parse(text)

    async def write_registers(self, values: dict[int, int]) -> None:
        """Write one or more 16-bit registers.

        Confirmed wire-format (captured from the official app):

            POST /api/write
            Content-Type: application/json
            {"1393":450, ...}         # string keys, integer values

            -> {"ver":"1.0","status":"OK","status_value":"0"}

        The firmware accepts a subset of registers, so a single-key map is fine.
        """
        body = {str(addr): int(value) & 0xFFFF for addr, value in values.items()}
        url = self._url("write")
        try:
            async with self._session.post(
                url,
                data=json.dumps(body),
                headers={"Content-Type": "application/json"},
                timeout=self._timeout,
            ) as resp:
                resp.raise_for_status()
                text = await resp.text()
        except aiohttp.ClientError as err:
            raise KospelPPE4ConnectionError(str(err)) from err

        status = _STATUS_RE.search(text)
        if not status or status.group(1) != "OK":
            raise KospelPPE4ProtocolError(text.strip())

    async def write_register(self, addr: int, value: int) -> None:
        """Write a single 16-bit register."""
        await self.write_registers({addr: value})
