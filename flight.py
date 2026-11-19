from clover import srv
from std_srvs.srv import Trigger
from clover.srv import SetLEDEffect
from led_msgs.msg import LEDStateArray
from led_msgs.srv import SetLEDs
from led_msgs.msg import LEDState
import rospy
import math

rospy.init_node('flight')

get_telemetry = rospy.ServiceProxy('get_telemetry', srv.GetTelemetry)
navigate = rospy.ServiceProxy('navigate', srv.Navigate)
land = rospy.ServiceProxy('land', Trigger)

set_effect = rospy.ServiceProxy('led/set_effect', SetLEDEffect, persistent=True)
set_leds = rospy.ServiceProxy('led/set_leds', SetLEDs, persistent=True)
led_count = None

def wait_nav():
    while not rospy.is_shutdown():
        telem = get_telemetry(frame_id='navigate_target')
        if math.sqrt(telem.x ** 2 + telem.y ** 2 + telem.z ** 2) < 0.2:
            return
        rospy.sleep(0.2)

def land_wait():
    land()
    while get_telemetry().armed:
        rospy.sleep(0.2)

def get_led_count():
    global led_count
    if led_count is None:
        led_count = len(rospy.wait_for_message('led/state', LEDStateArray, timeout=10).leds)
    return led_count

def police_blink():
    set_effect(effect='fill', r=0, g=0, b=0)
    for _ in range(3*2):
        for i in range(0, get_led_count()):
            if i % 2 == 0:
                set_leds([LEDState(index=int(i), r=51, g=51, b=255)])
            else:        
                set_leds([LEDState(index=int(i), r=255, g=0, b=0)])
                
        rospy.sleep(1/4)
        
        for i in range(0, get_led_count()):
            if i % 2 == 0:
                set_leds([LEDState(index=int(i), r=255, g=0, b=0)])
            else:
                set_leds([LEDState(index=int(i), r=51, g=51, b=255)])
                
        rospy.sleep(1/4)

navigate(x=0, y=0, z=1, frame_id='body', speed=0.5, auto_arm=True)
set_effect(effect='blink', r=0, g=255, b=0)
wait_nav()
home = get_telemetry('aruco_map')

set_effect(effect='fill', r=0, g=0, b=255)
navigate(x=0, y=2, z=1, frame_id='aruco_map', speed=0.5, auto_arm=True)
wait_nav()

police_blink()

set_effect(effect='fill', r=0, g=0, b=255)
navigate(x=home.x, y=home.y, z=home.z, frame_id='aruco_map', speed=0.5)
wait_nav()

land_wait()
