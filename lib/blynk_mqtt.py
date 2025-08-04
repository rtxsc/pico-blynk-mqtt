# SPDX-FileCopyrightText: 2024 Volodymyr Shymanskyy for Blynk Technologies Inc.
# SPDX-FileCopyrightText: 2025 ClumzyaziD for Robotronix Inc.
# SPDX-License-Identifier: Apache-2.0
#
# The software is provided "as is", without any warranties or guarantees (explicit or implied).
# This includes no assurances about being fit for any specific purpose.

import gc, sys, time, machine, json, asyncio
import config
from umqtt.simple import MQTTClient, MQTTException

def _dummy(*args):
    pass

on_connected = _dummy
on_disconnected = _dummy
on_message = _dummy
firmware_version = "4.8.2025"
firmware_datetime = "Monday 4 Aug 2025"

connected = False # change to global Mon 4 Aug 2025 22:39PM

LOGO = r"""
      ___  __          __
     / _ )/ /_ _____  / /__
    / _  / / // / _ \/  '_/
   /____/_/\_, /_//_/_/\_\
          /___/ RTXSC MicroPython for {} | v{} | Updated {}
""".format(sys.platform, firmware_version, firmware_datetime)

print(LOGO)

def _parse_url(url):
    try:
        scheme, url = url.split("://", 1)
    except ValueError:
        scheme = None
    try:
        netloc, path = url.split("/", 1)
    except ValueError:
        netloc, path = url, ""
    try:
        hostname, port = netloc.split(":", 1)
    except:
        hostname = netloc
    return scheme, hostname, int(port), path

def _on_message(topic, payload):
    topic = topic.decode("utf-8")
    payload = payload.decode("utf-8")

    if topic == "downlink/redirect":
        _, mqtt.server, mqtt.port, _ = _parse_url(payload)
        print("Redirecting...")
        mqtt.disconnect()  # Trigger automatic reconnect
    elif topic == "downlink/reboot":
        print("Rebooting...")
        machine.reset()
    elif topic == "downlink/ping":
        pass  # MQTT client library automagically sends the QOS1 response
    else:
        on_message(topic, payload)

ssl_ctx = None
if sys.platform in ("esp32", "rp2", "linux"):
    import ssl
    #print(ssl.MBEDTLS_VERSION)
    ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_ctx.verify_mode = ssl.CERT_REQUIRED
    # ISRG Root X1, expires: Mon, 04 Jun 2035 11:04:38 GMT
    ssl_ctx.load_verify_locations(cafile="ISRG_Root_X1.der")

mqtt = MQTTClient(client_id="", server=config.BLYNK_MQTT_BROKER, ssl=ssl_ctx,
                  user="device", password=config.BLYNK_AUTH_TOKEN, keepalive=45)
mqtt.set_callback(_on_message)

async def _mqtt_connect():
    try:
        mqtt.disconnect()
        gc.collect()
        print("Connecting to MQTT broker...")
        mqtt.connect()
        mqtt.subscribe("downlink/#")
        print("Connected to Blynk.Cloud", "[secure]" if ssl_ctx else "[insecure]")

        info = {
            "type": config.BLYNK_TEMPLATE_ID,
            "tmpl": config.BLYNK_TEMPLATE_ID,
            "ver":  firmware_version,
            "rxbuff": 1024
        }
        # Send info to the server
        # mqtt.publish("info/mcu", json.dumps(info)) # disabled 25 July 2025 Friday to save memory
    
        on_connected()
        return True
    except Exception as e:
        # sys.print_exception(e) # when we got [Errno 103] ECONNABORTED
        return False

async def socket_check_task():
    global connected
    while True:
        try:
            await asyncio.sleep_ms(5000)
            gc.collect()
            mqtt.check_socket() 
        except Exception as e:
            connected = False
            try:
                on_disconnected()
            except Exception as e:
                sys.print_exception(e)
        
async def task():
    global connected
    while True:
        await asyncio.sleep_ms(10)
        if not connected:
            if ssl_ctx:
                while not update_ntp_time():
                    print("Failed to update NTP...")
                    await asyncio.sleep(1)
            try:
                if await _mqtt_connect():
                    connected = True
                    print("[blynk_mqtt] MQTT connected")
                else:
                    connected = False
                    print("Waiting for WLAN/4G/5G network...")
                    await asyncio.sleep(1)

            except Exception as e:
                if isinstance(e, OSError):
                    print("Connection failed:", e)
                    await asyncio.sleep(1)
                elif isinstance(e, AttributeError):
                    print("Attribute Problem:", e)
                    pass  # This happens during reconnection
                elif isinstance(e, MQTTException) and (e.value == 4 or e.value == 5):
                    print("Invalid BLYNK_AUTH_TOKEN")
                    await asyncio.sleep(15 * 60)
                else:
                    sys.print_exception(e)
        else:
            try:
                mqtt.check_msg()
            except Exception as e:
                #sys.print_exception(e)
                connected = False
                try:
                    on_disconnected()
                except Exception as e:
                    sys.print_exception(e)

# Utilities

def time2str(t):
    y, m, d, H, M, S, w, j = t
    a = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")[w]
    return f"{a} {y}-{m:02d}-{d:02d} {H:02d}:{M:02d}:{S:02d}"

def update_ntp_time():
    Jan24 = 756_864_000 if (time.gmtime(0)[0] == 2000) else 1_704_067_200
    if time.time() > Jan24:
        return True

    print("Getting NTP time...")
    import ntptime
    try:
        ntptime.timeout = 5
        ntptime.settime()
        if time.time() > Jan24:
            print("UTC Time:", time2str(time.gmtime()))
            return True
    except Exception as e:
        print("NTP failed:", e)
    return False
