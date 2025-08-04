# SPDX-FileCopyrightText: 2024 Volodymyr Shymanskyy for Blynk Technologies Inc.
# SPDX-FileCopyrightText: 2025 ClumzyaziD for Robotronix Inc.
# SPDX-License-Identifier: Apache-2.0
#
# The software is provided "as is", without any warranties or guarantees (explicit or implied).
# This includes no assurances about being fit for any specific purpose.

"""
Basic Implementation
Improvised 4 Aug 2025 Monday - 23:58PM
"""

import sys, io, machine, time, asyncio
if sys.platform == "linux": sys.path.append("lib")
import config, blynk_mqtt
import demo


BLYNK_FIRMWARE_VERSION = "4.8.2025"

#
# App logic
#

mqtt = blynk_mqtt.mqtt

device = demo.Device(mqtt)

device.is_free_plan(True)

push_interval_hour = 1

anomaly_count = 0

async def publisher_task():
    while True:
        try:
            device.update()
        except Exception as e:
            print("[main] pub_task EXC:" + str(e))
        await asyncio.sleep_ms(push_interval_hour*3600*1000)
    
def mqtt_connected():
    print("[main] MQTT connected")
    device.connected()

def mqtt_disconnected():
    global anomaly_count
    anomaly_count += 1
    print("[main] MQTT disconnected | Anomaly #{}".format(anomaly_count))
    if anomaly_count == 3:
        offline_mode(60)

def mqtt_callback(topic, payload):
    print(f"[main] Got: {topic}, value: {payload}")
    device.process_message(topic, payload)

#
# Main loop
#

blynk_mqtt.on_connected = mqtt_connected
blynk_mqtt.on_disconnected = mqtt_disconnected
blynk_mqtt.on_message = mqtt_callback
blynk_mqtt.firmware_version = BLYNK_FIRMWARE_VERSION


def connect_wifi():   
    import network
    wlan = network.WLAN(network.STA_IF)
    max_wait = 10
    if not wlan.isconnected():
        print(f"[main] Connecting to {config.WIFI_SSID}\n", end="")
        wlan.active(True)
        wlan.disconnect()
        # wlan.config(reconnects=5)
        wlan.connect(config.WIFI_SSID, config.WIFI_PASS)

        while not wlan.isconnected() and max_wait > 0:
            time.sleep(1)
            print(".", end="")
            max_wait -= 1
            if wlan.status() == network.STAT_NO_AP_FOUND:
                raise Exception("WiFi Access Point not found")
            if wlan.status() == network.STAT_WRONG_PASSWORD:
                raise Exception("Wrong WiFi credentials")
            if wlan.status() == network.STAT_IDLE:
                raise Exception("no connection and no activity")
            if wlan.status() == network.STAT_CONNECT_FAIL:
                raise Exception("failed due to other problems")
            
            # these two cannot be active during deployment
            # only permissible via thonny execution (run via play button)
            # discovered 12:30AM Thu 31 July at TBS
            # changed to print instead of raise
            
#             if wlan.status() == network.STAT_CONNECTING:
#                 print("connecting in progress")
#             if wlan.status() == network.STAT_GOT_IP:
#                 print("connection successful")
             
        print("[main] OK:", wlan.ifconfig()[0])

    else:
        # successfully connected
        print("[main-else] OK:", wlan.ifconfig()[0])
        max_wait = 10 # reset after success

def offline_mode(seconds=60):
    start = 0
    time.sleep(2)
    print("entering OFFLINE mode")
    while(start < seconds):
        start += 1
        print("offline for {} sec".format(start))
        time.sleep(1)
    print("exiting OFFLINE mode...restarting now")
    time.sleep(1)
    machine.reset() # MASTER REBOOT

if sys.platform != "linux":
    try:
        connect_wifi()
    except Exception as e:
        print(e) # put this on OLED later on
        pass # ignore first exception upon connection

if __name__ == "__main__":
    try:
        asyncio.run(asyncio.gather(
            blynk_mqtt.task(),
            blynk_mqtt.socket_check_task(),
            publisher_task()
        ))
    except Exception as e:
        print("[__main__ EXP]:", e)
    except KeyboardInterrupt:
        print("Keyboard Interrupted | STOP was pressed")
    finally:
        # Clean up and create a new event loop
        print("[__main__  Clean up and create a new event loop]")
        asyncio.new_event_loop()

