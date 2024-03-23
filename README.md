# ledble-ledlamp

Another set of extremely low priced LEDs.  These ones cost me £1.60 plus tax for a 5M strip with an IR remote and Bluetooth control.  The price has since increased.  I got them in the Anniversary Sale.

![image](https://github.com/8none1/ledble-ledlamp/assets/6552931/5055edfb-6705-41d6-8384-d12797efa29f)

<https://www.aliexpress.com/item/1005006368669067.html>

![image](https://github.com/8none1/ledble-ledlamp/assets/6552931/b36094f9-d6a8-45fc-b81b-b41ad34a4169)

This Home Assistant integration supports LEDBLE lights which use the `LED Lamp` app over Bluetooth LE.  My device advertises the name `LEDBLE-01-9201`.  I only have one device that uses this controller at the moment, so I don't know if this changes (specifically the last four digits) but I don't expect it will. i.e. this name is probably fixed.

They provide write characteristic `0xFFE1`.

There is an interesting problem with these lights in that the name they advertise matches another set of lights with a different controller.  The default LED BLE Home Assistant integration tries to connect to these lights but doesn't speak the right protocol and doesn't try to connect to the right characteristic resulting in a blanket error.  A better fix would be to update the Home Assistant core integration to support these lights, but that would involve adding support to three other projects first, and it's a real spaghetti of indirection, so I can't be bothered.  There is an issue open [here](https://github.com/home-assistant/core/issues/105338#issuecomment-2010342769) but I doubt anything will happen with it.
So this integration exists.  I don't yet know how they will co-exist.  We will soon find out.

## Bluetooth LE Protocol

The protocol for these lights is pretty easy to understand.  All packets type the format of:

```text
|---|----------------------- header
|   | ||-------------------- action to take
|   | || |---------|-------- data
|   | || |         | |---|-- footer
7e ff 05 03 ff 00 00 ff ef
```

### Brightness

Action: `01`

```text
|---|----------------------- header
|   | ||-------------------- Brightness action (01)
|   | || ||----------------- Brightness (0-100, 0x0 - 0x64)
|   | || ||          |---|-- footer
7e ff 01 60 00 ff ff ff ef
7e ff 01 21 00 ff ff ff ef
7e ff 01 04 00 ff ff ff ef
7e ff 01 45 00 ff ff ff ef
7e ff 01 61 00 ff ff ff ef
```

### Speed

Action: `02`

```text
|---|----------------------- header
|   | ||-------------------- Speed action (02)
|   | || ||----------------- Speed (0-100, 0x0 - 0x64)
|   | || ||          |---|-- footer
7e ff 02 60 00 ff ff ff ef
7e ff 02 21 00 ff ff ff ef
7e ff 02 04 00 ff ff ff ef
7e ff 02 45 00 ff ff ff ef
7e ff 02 61 00 ff ff ff ef
```

### Mode / Effects

Action: `03`

```text
|---|----------------------- header
|   | ||-------------------- Mode action (03)
|   | || ||----------------- Effect number (0x87-0x9d) (here be dragons)
|   | || ||          |---|-- footer
7e ff 03 87 03 ff ff ff ef
7e ff 03 87 03 ff ff ff ef
7e ff 03 88 03 ff ff ff ef
7e ff 03 88 03 ff ff ff ef
7e ff 03 89 03 ff ff ff ef
7e ff 03 9d 03 ff ff ff ef
```

### Power

Action: `04`

`7e ff 04 01 ff ff ff ff ef` - On

`7e ff 04 00 ff ff ff ff ef` - Off

### Colour

Action: `05`

```text
|---|----------------------- header
|   | ||-------------------- RGB action (05)
|   | ||    ||-------------- red
|   | ||    || ||----------- green
|   | ||    || || ||-------- blue
|   | ||    || || || |---|----- footer
7e ff 05 03 ff 00 00 ff ef
7e ff 05 03 00 ff 00 ff ef
7e ff 05 03 00 00 ff ff ef
7e ff 05 03 ff 00 00 ff ef
7e ff 05 03 00 ff 00 ff ef
7e ff 05 03 00 00 ff ff ef
```

## Other projects that might be of interest

- [iDotMatrix](https://github.com/8none1/idotmatrix)
- [Zengge LEDnet WF](https://github.com/8none1/zengge_lednetwf)
- [iDealLED](https://github.com/8none1/idealLED)
- [BJ_LED](https://github.com/8none1/bj_led)
- [ELK BLEDOB](https://github.com/8none1/elk-bledob)
- [HiLighting LED](https://github.com/8none1/hilighting_homeassistant)
- [BLELED LED Lamp](https://github.com/8none1/ledble-ledlamp)
