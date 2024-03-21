# ledble-ledlamp

Home Assistant integration for LEDBLE lights which use the `LED Lamp` app over Bluetooth LE.

Another set of extremely low priced LEDs.  These ones cost me £1.60 plus tax for a 5M strip with an IR remote and Bluetooth control.

The price has since increased.  I got them in the Anniversary Sale.

https://www.aliexpress.com/item/1005006368669067.html

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
