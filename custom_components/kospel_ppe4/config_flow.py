"""Config flow for Kospel PPE4."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import KospelPPE4Client, KospelPPE4Error
from .const import CONF_HOST, DEFAULT_NAME, DOMAIN, REG_SERIAL_SUFFIX

STEP_USER_SCHEMA = vol.Schema({vol.Required(CONF_HOST): str})


class KospelPPE4ConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Kospel PPE4."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            session = async_get_clientsession(self.hass)
            client = KospelPPE4Client(host, session)
            try:
                regs = await client.read_registers(REG_SERIAL_SUFFIX, 1)
            except KospelPPE4Error:
                errors["base"] = "cannot_connect"
            else:
                suffix = regs.get(REG_SERIAL_SUFFIX)
                if suffix is None:
                    errors["base"] = "not_ppe4"
                else:
                    serial = f"ppe4_{suffix:08d}"
                    await self.async_set_unique_id(serial)
                    self._abort_if_unique_id_configured(
                        updates={CONF_HOST: host}
                    )
                    return self.async_create_entry(
                        title=f"{DEFAULT_NAME} ({serial})",
                        data={CONF_HOST: host},
                    )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )
