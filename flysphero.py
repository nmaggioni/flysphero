#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from configparser import ConfigParser
from math import pi
from numpy import interp
from spheropy.Sphero import Sphero
from spheropy.DataStream import DataStreamManager
import datetime
import logging
import pigpio
import signal
import sys
import time

sphero_pitch = sphero_roll = sphero_yaw = 0

dsm = DataStreamManager()
dsm.imu_angle = True

_ppm_running = False
_output = ()

config = ConfigParser()
config.read('config.ini')

SPHERO_NAME = config.get('flysphero', 'name')
SPHERO_MAC = config.get('flysphero', 'mac')
PPM_OUTPUT_PIN = config.get('flysphero', 'ppm_output_pin')


def ensure_int_is_in_range(n, min, max):
    if min <= n <= max:
        return n
    elif n < min:
        return min
    elif n > max:
        return max


def map_sphero_angle_to_rc(n, old_min, old_max):
    return interp(ensure_int_is_in_range(int(n), old_min, old_max), [old_min, old_max], [-1, 1])


def get_sphero_angle(channel):
    global sphero_pitch, sphero_roll, sphero_yaw
    if channel is "pitch":
        return map_sphero_angle_to_rc(sphero_pitch, -90, 90)
    if channel is "roll":
        return map_sphero_angle_to_rc(sphero_roll, -80, 85)
    if channel is "yaw":
        return map_sphero_angle_to_rc(sphero_yaw, -180, 179)


def sphero_sensors_callback(sensor_data):
    global sphero_pitch, sphero_roll, sphero_yaw
    for frame in sensor_data:
        sphero_pitch = frame['imu_angle'].pitch * (180 / pi)
        sphero_roll = frame['imu_angle'].roll * (180 / pi)
        sphero_yaw = frame['imu_angle'].yaw * (180 / pi)
        #date = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        #print("{} - Pitch: {: 06.2f}°, Roll: {: 06.2f}°, Yaw: {: 06.2f}°".format(date, sphero_pitch, sphero_roll, sphero_yaw))


def main():
    print("A) Setting up I/O")
    print("A.1) Configuring PPM pin")
    pi_gpio = 1 << PPM_OUTPUT_PIN
    print("A.2) Creating instance")
    pi = pigpio.pi()
    print("A.3) Setting output mode")
    pi.set_mode(PPM_OUTPUT_PIN, pigpio.OUTPUT)
    print("A.4) Configuring wave parameters")
    pi.wave_add_generic([pigpio.pulse(pi_gpio, 0, 2000)])
    waves = [None, None, pi.wave_create()]
    pi.wave_send_repeat(waves[-1])

    print("B) Setting up Sphero")
    print("B.1) Creating instance")
    s = Sphero(SPHERO_NAME, SPHERO_MAC)
    print("B.2) Connecting to device")
    s.connect()
    print("B.3) Starting communications")
    s.start()
    print("B.4) Configuring colors")
    s.set_color(255, 0, 0)
    time.sleep(1)
    s.set_color(0, 255, 0)
    time.sleep(1)
    s.set_color(0, 0, 255)
    time.sleep(1)
    s.set_color(0, 0, 0)
    s.set_back_light(255)
    print("B.5.1) Enabling stabilization")
    s.set_stabilization(True)
    print("B.5.2) Place level now! (6s)")
    for i in range(6):
        s.set_color(255, 255, 255)
        time.sleep(0.5)
        s.set_color(0, 0, 0)
        time.sleep(0.5)
    print("B.5.3) Disabling stabilization")
    s.set_stabilization(False)
    print("B.6) Registering sensors callback")
    s.register_sensor_callback(sphero_sensors_callback)
    print("B.7) Requesting sensors stream")
    s.set_data_stream(dsm, frequency=10)

    print("C) Enabling PPM generation")
    _ppm_running = True
    print("------------------------------------")

    prev = None
    while _ppm_running:
        _output = (get_sphero_angle("pitch"), get_sphero_angle("roll"))
        #print(_output)
        if _output == prev:
            pass
        else:
            pulses, pos = [], 0
            for value in _output:
                us = int(round(1333 + 453 * value))
                pulses += [pigpio.pulse(0, pi_gpio, 300), pigpio.pulse(pi_gpio, 0, us - 300)]
                pos += us
            pulses += [pigpio.pulse(0, pi_gpio, 300), pigpio.pulse(pi_gpio, 0, 20000 - 300 - pos - 1)]
            pi.wave_add_generic(pulses)
            waves.append(pi.wave_create())
            pi.wave_send_using_mode(waves[-1], pigpio.WAVE_MODE_REPEAT_SYNC)
            last, waves = waves[0], waves[1:]
            if last:
                pi.wave_delete(last)
        time.sleep(.02)


def shutdown(signum, frame):
    global _ppm_running
    _ppm_running = False
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    try:
        main()
    except KeyboardInterrupt:
        shutdown(None, None)
