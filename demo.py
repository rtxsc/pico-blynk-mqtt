# SPDX-FileCopyrightText: 2024 Volodymyr Shymanskyy for Blynk Technologies Inc.
# SPDX-FileCopyrightText: 2025 ClumzyaziD for Robotronix Inc.
# SPDX-License-Identifier: Apache-2.0
#
# The software is provided "as is", without any warranties or guarantees (explicit or implied).
# This includes no assurances about being fit for any specific purpose.

"""
4 Aug 2025 Monday
"""

import random
import sys
from machine import Pin, ADC

led = Pin("LED", Pin.OUT)
vsys_pin = ADC(Pin(29))

def get_vsys():
    adc_reading = vsys_pin.read_u16()
    adc_volt = (adc_reading * 3.3)/65535
    vsys_volt = adc_volt * 3
    if vsys_volt <= 3.0:
        vsys_volt = 3.0
    if vsys_volt >= 4.2:
        vsys_volt = 4.2 
    return vsys_volt

firmware_version = "4.8.2025"
LOGO = r"""
      ___  __          __
     / _ )/ /_ _____  / /__
    / _  / / // / _ \/  '_/
   /____/_/\_, /_//_/_/\_\
          /___/ MicroPython Device Demo for {} | v{}
""".format(sys.platform, firmware_version)

class Device:
    free_plan = True
    power_on = False
    target_temp = 23    # Target temperature, can be set from 10 to 30
    current_temp = 15   # Initial current temperature
    
    temp_ahtx = 0
    humi_ahtx = 0
    uptime = 0
    pushIntervalSecond = 3600
    mqtt_published = 0
    elapse = "HH:MM:SS"
    mqtt_reconnect = 0
    settemp_disabled = 0
    vsys_volt = 0.0
    
    def __init__(self, mqtt):
        self.mqtt = mqtt

    def is_free_plan(self, value):
        self.free_plan = True if bool(value) else False

    def connected(self):
        self.mqtt_reconnect += 1
        # Get latest settings from Blynk.Cloud
        if not self.free_plan:
            self.mqtt.publish("get/ds", "Power,Set Temperature") # discovered Wed 23 July 2025

        # Display Blynk logo, just for fun
        self.terminal_print(LOGO)
        self.terminal_print("Type \"help\" for the list of available commands")

    def terminal_print(self, *args):
        if not self.free_plan:
            self.mqtt.publish("ds/Terminal", " ".join(map(str, args)) + "\n") # disabled 25 July Friday

    def process_message(self, topic, payload):
        if topic == "downlink/ds/Power":
            self.power_on = bool(int(payload))
            settemp_disabled = 0 if self.power_on else 1
            if payload == "1":
                led.on()
            else:
                led.off()
            if not self.free_plan:
                self.mqtt.publish("ds/Set Temperature/prop/isDisabled", settemp_disabled)
        elif topic == "downlink/ds/Set Temperature":
            self.target_temp = float(payload)
        elif topic == "downlink/ds/FastUpdate":
            self.terminal_print("Fast Update via V8 Button Requested")
            self.update()
        elif topic == "downlink/ds/RGBslider":
            pass
        elif topic == "downlink/ds/getVsys":
            self.vsys_volt = get_vsys()
            print("Batt:{} Percent:{}".format(self.vsys_volt))
        elif topic == "downlink/ds/Terminal":
            cmd = list(filter(len, payload.split()))
            if cmd[0] == "set":
                self.target_temp = int(cmd[1])
                if not self.free_plan:
                    self.mqtt.publish("ds/Set Temperature", self.target_temp)
                self.terminal_print(f"Temperature set to {self.target_temp}")
            elif cmd[0] == "on":
                self.power_on = True
                if not self.free_plan:
                    self.mqtt.publish("ds/Power", 1)
                self.terminal_print("Turned ON")
            elif cmd[0] == "off":
                self.power_on = False
                if not self.free_plan:
                    self.mqtt.publish("ds/Power", 0)
                self.terminal_print("Turned OFF")
            elif cmd[0] == "fast":
                self.terminal_print("Fast Update Requested")
                self.update()
            elif cmd[0] in ("help", "?"):
                self.terminal_print("Available commands:")
                self.terminal_print("  set N    - set target temperature")
                self.terminal_print("  on       - turn on")
                self.terminal_print("  off      - turn off")
            else:
                self.terminal_print(f"Unknown command: {cmd[0]}")

    def _update_temperature_mqtt(self):
        target = self.target_temp if self.power_on else 10
        next_temp = self.current_temp + (target - self.current_temp) * 0.05
        next_temp = max(10, min(next_temp, 35))
        next_temp += (0.5 - random.uniform(0, 1)) * 0.3
        self.current_temp = next_temp
        self.mqtt.publish("ds/Current Temperature", self.current_temp) # consume 2 message unit
        
        
    def _update_uptime_elapse(self):
        self.mqtt.publish("ds/elapseString", self.elapse )
        
    def _update_widget_state_mqtt(self):
        if not self.power_on:
            state = 1 # OFF
        elif abs(self.current_temp - self.target_temp) < 1.0:
            state = 2 # Idle
        elif self.target_temp > self.current_temp:
            state = 3 # Heating
        elif self.target_temp < self.current_temp:
            state = 4 # Cooling

        state_colors = [None, "E4F6F7", "E6F7E4", "F7EAE4", "E4EDF7"]
        self.mqtt.publish("ds/Status", state) # consume 2 message unit
        self.mqtt.publish("ds/Status/prop/color", state_colors[state]) # consume 2 message unit

    def update(self):
        self.mqtt_published += 1
        self._update_temperature_mqtt()
        self._update_widget_state_mqtt()

    

        

        