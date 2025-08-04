
# Blynk MQTT client for MicroPython
### pico-blynk-mqtt
Repo for my work on Raspberry Pi Pico W / 2W with Blynk MQTT via MicroPython
---
This example was verified to work with `MicroPython v1.25.0` on:
- `Raspberry Pi Pico W` (RP2040)
- `Raspberry Pi Pico 2W` (RP2350)

## Prepare your Device in Blynk.Cloud

1. Create Blynk template based on the provided blueprint. Click the **`Use Blueprint`** button in [`MQTT Air Cooler/Heater Demo`](https://blynk.cloud/dashboard/blueprints/Library/TMPL4zGiS1A7l).
2. In the left panel, select `Devices`
3. Click `New Device` button
4. Select `From Template -> MQTT Demo`, and click **`Create`**

> [!NOTE]
> Please note the device credentials that appear in the upper right corner. You'll need them in the next step.

## 1. Install `MicroPython`

https://micropython.org/download

## 2. Edit `config.py`

Set your WiFi and [Blynk device credentials](https://docs.blynk.io/en/getting-started/activating-devices/manual-device-activation#getting-auth-token).

## 3. Install required libraries

Make sure your board is **connected via USB**. It should **not** be opened by any serial monitor. without any board connected, you would see **mpremote: no device found** error.

Run these commands on your development machine (Terminal on macOS):

```sh
# Install mpremote utility
pip3 install --upgrade mpremote
# Install libraries
mpremote cp -r ./lib :
# Copy the example files to the device
mpremote cp *.py *.der :
```

## 4. Run

Reset you board and open MicroPython REPL:

```sh
mpremote repl
```

The device should get connected in a few seconds:

```log
      ___  __          __
     / _ )/ /_ _____  / /__
    / _  / / // / _ \/  '_/
   /____/_/\_, /_//_/_/\_\
          /___/

Connecting to WiFi_SSID... OK: 192.168.1.123
Connecting to MQTT broker...
Connected to Blynk.Cloud [secure]
```

# Running on linux

This will also work on Linux-based PCs or SBCs like Raspberry Pi:

```sh
micropython main.py
```

---

## Further reading

- [Blynk MQTT API documentation](https://docs.blynk.io/en/blynk.cloud-mqtt-api/device-mqtt-api)
- [`asyncio` documentation](https://docs.micropython.org/en/latest/library/asyncio.html)
- [`asyncio` tutorial](https://github.com/peterhinch/micropython-async/blob/master/v3/docs/TUTORIAL.md)
- [`mpremote` documentation](https://docs.micropython.org/en/latest/reference/mpremote.html)
- Alternative MQTT libraries like [mqtt_as](https://github.com/peterhinch/micropython-mqtt/tree/master/mqtt_as)
- [Blynk Troubleshooting guide](https://docs.blynk.io/en/troubleshooting/general-issues)
- [Blynk Documentation](https://docs.blynk.io/en)