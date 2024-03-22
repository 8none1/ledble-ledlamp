import asyncio
from homeassistant.components import bluetooth
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.components.light import (ColorMode)
from bleak.backends.device import BLEDevice
from bleak.backends.service import BleakGATTCharacteristic, BleakGATTServiceCollection
from bleak.exc import BleakDBusError
from bleak_retry_connector import BLEAK_RETRY_EXCEPTIONS as BLEAK_EXCEPTIONS
from bleak_retry_connector import (
    BleakClientWithServiceCache,
    BleakNotFoundError,
    establish_connection,
)
from typing import Any, TypeVar, cast, Tuple
from collections.abc import Callable
#import traceback
import logging
import colorsys


LOGGER = logging.getLogger(__name__)
EFFECT_0x87 = "Effect 0x87"
EFFECT_0x88 = "Effect 0x88"
EFFECT_0x89 = "Effect 0x89"
EFFECT_0x8a = "Effect 0x8a"
EFFECT_0x8b = "Effect 0x8b"
EFFECT_0x8c = "Effect 0x8c"
EFFECT_0x8d = "Effect 0x8d"
EFFECT_0x8e = "Effect 0x8e"
EFFECT_0x8f = "Effect 0x8f"
EFFECT_0x90 = "Effect 0x90"
EFFECT_0x91 = "Effect 0x91"
EFFECT_0x92 = "Effect 0x92"
EFFECT_0x93 = "Effect 0x93"
EFFECT_0x94 = "Effect 0x94"
EFFECT_0x95 = "Effect 0x95"
EFFECT_0x96 = "Effect 0x96"
EFFECT_0x97 = "Effect 0x97"
EFFECT_0x98 = "Effect 0x98"
EFFECT_0x99 = "Effect 0x99"
EFFECT_0x9a = "Effect 0x9a"
EFFECT_0x9b = "Effect 0x9b"
EFFECT_0x9c = "Effect 0x9c"
EFFECT_0x9d = "Effect 0x9d"

EFFECT_MAP = {
    EFFECT_0x87:    (0x87),
    EFFECT_0x88:    (0x88),
    EFFECT_0x89:    (0x89),
    EFFECT_0x8a:    (0x8a),
    EFFECT_0x8b:    (0x8b),
    EFFECT_0x8c:    (0x8c),
    EFFECT_0x8d:    (0x8d),
    EFFECT_0x8e:    (0x8e),
    EFFECT_0x8f:    (0x8f),
    EFFECT_0x90:    (0x90),
    EFFECT_0x91:    (0x91),
    EFFECT_0x92:    (0x92),
    EFFECT_0x93:    (0x93),
    EFFECT_0x94:    (0x94),
    EFFECT_0x95:    (0x95),
    EFFECT_0x96:    (0x96),
    EFFECT_0x97:    (0x97),
    EFFECT_0x98:    (0x98),
    EFFECT_0x99:    (0x99),
    EFFECT_0x9a:    (0x9a),
    EFFECT_0x9b:    (0x9b),
    EFFECT_0x9c:    (0x9c),
    EFFECT_0x9d:    (0x9d)
}

EFFECT_LIST = sorted(EFFECT_MAP)
EFFECT_ID_NAME = {v: k for k, v in EFFECT_MAP.items()}

NAME_ARRAY = ["LEDBLE-01"]
WRITE_CHARACTERISTIC_UUIDS = ["0000ffe1-0000-1000-8000-00805f9b34fb"]
TURN_ON_CMD  = [bytearray.fromhex("7e ff 04 01 ff ff ff ff ef")]
TURN_OFF_CMD = [bytearray.fromhex("7e ff 04 00 ff ff ff ff ef")]
DEFAULT_ATTEMPTS = 3
BLEAK_BACKOFF_TIME = 0.25
RETRY_BACKOFF_EXCEPTIONS = (BleakDBusError)

WrapFuncType = TypeVar("WrapFuncType", bound=Callable[..., Any])

def retry_bluetooth_connection_error(func: WrapFuncType) -> WrapFuncType:
    async def _async_wrap_retry_bluetooth_connection_error(
        self: "LEDBLELEDLamp", *args: Any, **kwargs: Any
    ) -> Any:
        attempts = DEFAULT_ATTEMPTS
        max_attempts = attempts - 1

        for attempt in range(attempts):
            try:
                return await func(self, *args, **kwargs)
            except BleakNotFoundError:
                # The lock cannot be found so there is no
                # point in retrying.
                raise
            except RETRY_BACKOFF_EXCEPTIONS as err:
                if attempt >= max_attempts:
                    LOGGER.debug(
                        "%s: %s error calling %s, reach max attempts (%s/%s)",
                        self.name,
                        type(err),
                        func,
                        attempt,
                        max_attempts,
                        exc_info=True,
                    )
                    raise
                LOGGER.debug(
                    "%s: %s error calling %s, backing off %ss, retrying (%s/%s)...",
                    self.name,
                    type(err),
                    func,
                    BLEAK_BACKOFF_TIME,
                    attempt,
                    max_attempts,
                    exc_info=True,
                )
                await asyncio.sleep(BLEAK_BACKOFF_TIME)
            except BLEAK_EXCEPTIONS as err:
                if attempt >= max_attempts:
                    LOGGER.debug(
                        "%s: %s error calling %s, reach max attempts (%s/%s): %s",
                        self.name,
                        type(err),
                        func,
                        attempt,
                        max_attempts,
                        err,
                        exc_info=True,
                    )
                    raise
                LOGGER.debug(
                    "%s: %s error calling %s, retrying  (%s/%s)...: %s",
                    self.name,
                    type(err),
                    func,
                    attempt,
                    max_attempts,
                    err,
                    exc_info=True,
                )

    return cast(WrapFuncType, _async_wrap_retry_bluetooth_connection_error)


class LEDBLELEDLamp:
    def __init__(self, address, hass) -> None:
        self.loop = asyncio.get_running_loop()
        self._mac = address
        self._hass = hass
        self._delay = 5
        self._device: BLEDevice | None = None
        self._device = bluetooth.async_ble_device_from_address(self._hass, address)
        if not self._device:
            raise ConfigEntryNotReady(
                f"You need to add bluetooth integration (https://www.home-assistant.io/integrations/bluetooth) or couldn't find a nearby device with address: {address}"
            )
        self._connect_lock: asyncio.Lock = asyncio.Lock()
        self._client: BleakClientWithServiceCache | None = None
        self._disconnect_timer: asyncio.TimerHandle | None = None
        self._cached_services: BleakGATTServiceCollection | None = None
        self._expected_disconnect = False
        self._is_on = None
        self._rgb_color = None
        self._brightness = 255
        self._effect = None
        self._effect_speed = 0x64
        self._color_mode = ColorMode.RGB
        self._write_uuid = None
        self._turn_on_cmd = None
        self._turn_off_cmd = None
        self._model = self._detect_model()
        
        LOGGER.debug(
            "Model information for device %s : ModelNo %s. MAC: %s",
            self._device.name,
            self._model,
            self._mac,
        )

    def _detect_model(self):
        x = 0
        for name in NAME_ARRAY:
            if self._device.name.lower().startswith(name.lower()):
                self._turn_on_cmd = TURN_ON_CMD[x]
                self._turn_off_cmd = TURN_OFF_CMD[x]
                return x
            x = x + 1

    async def _write(self, data: bytearray):
        """Send command to device and read response."""
        await self._ensure_connected()
        await self._write_while_connected(data)

    async def _write_while_connected(self, data: bytearray):
        LOGGER.debug(f"Writing data to {self.name}: {data.hex()}")
        await self._client.write_gatt_char(self._write_uuid, data, False)
    
    @property
    def mac(self):
        return self._device.address

    @property
    def reset(self):
        return 0

    @property
    def name(self):
        return self._device.name

    @property
    def rssi(self):
        return self._device.rssi

    @property
    def is_on(self):
        return self._is_on

    @property
    def brightness(self):
        return self._brightness 

    @property
    def rgb_color(self):
        return self._rgb_color

    @property
    def effect_list(self) -> list[str]:
        return EFFECT_LIST

    @property
    def effect(self):
        return self._effect
    
    @property
    def color_mode(self):
        return self._color_mode

    @retry_bluetooth_connection_error
    async def set_rgb_color(self, rgb: Tuple[int, int, int], brightness: int | None = None):
        self._rgb_color = rgb
        if brightness is None:
            if self._brightness is None:
                self._brightness = 255
            else:
                brightness = self._brightness
        brightness_percent = int(brightness * 100 / 255)
        # RGB packet
        rgb_packet = bytearray.fromhex("7e ff 05 03")
        rgb_packet.append(rgb[0])
        rgb_packet.append(rgb[1])
        rgb_packet.append(rgb[2])
        rgb_packet.append(0xff)
        rgb_packet.append(0xef)
        await self._write(rgb_packet)

    async def set_brightness_local(self, value: int):
        self._brightness = value
        await self.set_rgb_color(self._rgb_color, value)

    @retry_bluetooth_connection_error
    async def turn_on(self):
        await self._write(self._turn_on_cmd)
        self._is_on = True
                
    @retry_bluetooth_connection_error
    async def turn_off(self):
        await self._write(self._turn_off_cmd)
        self._is_on = False

    @retry_bluetooth_connection_error
    async def set_effect(self, effect: str):
        if effect not in EFFECT_LIST:
            LOGGER.error("Effect %s not supported", effect)
            return
        self._effect = effect
        effect_packet = bytearray.fromhex("7e ff 03")
        effect_id = EFFECT_MAP.get(effect)
        LOGGER.debug('Effect ID: %s', effect_id)
        LOGGER.debug('Effect name: %s', effect)
        effect_packet.append(effect_id)
        effect_packet.append(0x03, 0xff, 0xff, 0xff, 0xef)
        await self._write(effect_packet)

    @retry_bluetooth_connection_error
    async def turn_on(self):
        await self._write(self._turn_on_cmd)
        self._is_on = True

    @retry_bluetooth_connection_error
    async def turn_off(self):
        await self._write(self._turn_off_cmd)
        self._is_on = False

    @retry_bluetooth_connection_error
    async def update(self):
        LOGGER.debug("%s: Update in ledble-ledlamp called", self.name)
        # I dont think we have anything to update

    async def _ensure_connected(self) -> None:
        """Ensure connection to device is established."""
        if self._connect_lock.locked():
            LOGGER.debug(
                "%s: Connection already in progress, waiting for it to complete",
                self.name,
            )
        if self._client and self._client.is_connected:
            self._reset_disconnect_timer()
            return
        async with self._connect_lock:
            # Check again while holding the lock
            if self._client and self._client.is_connected:
                self._reset_disconnect_timer()
                return
            LOGGER.debug("%s: Connecting", self.name)
            client = await establish_connection(
                BleakClientWithServiceCache,
                self._device,
                self.name,
                self._disconnected,
                cached_services=self._cached_services,
                ble_device_callback=lambda: self._device,
            )
            LOGGER.debug("%s: Connected", self.name)
            resolved = self._resolve_characteristics(client.services)
            if not resolved:
                # Try to handle services failing to load
                #resolved = self._resolve_characteristics(await client.get_services())
                resolved = self._resolve_characteristics(client.services)
            self._cached_services = client.services if resolved else None

            self._client = client
            self._reset_disconnect_timer()

    def _resolve_characteristics(self, services: BleakGATTServiceCollection) -> bool:
        """Resolve characteristics."""
        for characteristic in WRITE_CHARACTERISTIC_UUIDS:
            if char := services.get_characteristic(characteristic):
                self._write_uuid = char
                break
        return bool(self._write_uuid)

    def _reset_disconnect_timer(self) -> None:
        """Reset disconnect timer."""
        if self._disconnect_timer:
            self._disconnect_timer.cancel()
        self._expected_disconnect = False
        if self._delay is not None and self._delay != 0:
            LOGGER.debug(
                "%s: Configured disconnect from device in %s seconds",
                self.name,
                self._delay
            )
            self._disconnect_timer = self.loop.call_later(self._delay, self._disconnect)

    def _disconnected(self, client: BleakClientWithServiceCache) -> None:
        """Disconnected callback."""
        if self._expected_disconnect:
            LOGGER.debug("%s: Disconnected from device", self.name)
            return
        LOGGER.warning("%s: Device unexpectedly disconnected", self.name)

    def _disconnect(self) -> None:
        """Disconnect from device."""
        self._disconnect_timer = None
        asyncio.create_task(self._execute_timed_disconnect())

    async def stop(self) -> None:
        """Stop the LEDBLE."""
        LOGGER.debug("%s: Stop", self.name)
        await self._execute_disconnect()

    async def _execute_timed_disconnect(self) -> None:
        """Execute timed disconnection."""
        LOGGER.debug(
            "%s: Disconnecting after timeout of %s",
            self.name,
            self._delay
        )
        await self._execute_disconnect()

    async def _execute_disconnect(self) -> None:
        """Execute disconnection."""
        async with self._connect_lock:
            client = self._client
            self._expected_disconnect = True
            self._client = None
            self._write_uuid = None
            if client and client.is_connected:
                await client.disconnect()
            LOGGER.debug("%s: Disconnected", self.name)
    