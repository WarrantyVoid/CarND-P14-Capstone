#!/usr/bin/env python

import rospy
from std_msgs.msg import Bool
from dbw_mkz_msgs.msg import ThrottleCmd, SteeringCmd, BrakeCmd, SteeringReport
from geometry_msgs.msg import TwistStamped
from twist_controller import Controller
import math

GAS_DENSITY = 2.588


'''
You can build this node only after you have built (or partially built) the `waypoint_updater` node.

You will subscribe to `/twist_cmd` message which provides the proposed linear and angular velocities.
You can subscribe to any other message that you find important or refer to the document for list
of messages subscribed to by the reference implementation of this node.

One thing to keep in mind while building this node and the `twist_controller` class is the status
of `dbw_enabled`. While in the simulator, its enabled all the time, in the real car, that will
not be the case. This may cause your PID controller to accumulate error because the car could
temporarily be driven by a human instead of your controller.

We have provided two launch files with this node. Vehicle specific values (like vehicle_mass,
wheel_base) etc should not be altered in these files.

We have also provided some reference implementations for PID controller and other utility classes.
You are free to use them or build your own.

Once you have the proposed throttle, brake, and steer values, publish it on the various publishers
that we have created in the `__init__` function.

'''

from twist_controller import vector_magnitude

class DBWNode(object):
    def __init__(self):
        rospy.init_node('dbw_node')

        vehicle_mass = rospy.get_param('~vehicle_mass', 1736.35)
        fuel_capacity = rospy.get_param('~fuel_capacity', 13.5)
        brake_deadband = rospy.get_param('~brake_deadband', .1)
        decel_limit = rospy.get_param('~decel_limit', -5)
        accel_limit = rospy.get_param('~accel_limit', 1.)
        wheel_radius = rospy.get_param('~wheel_radius', 0.2413)
        wheel_base = rospy.get_param('~wheel_base', 2.8498)
        steer_ratio = rospy.get_param('~steer_ratio', 14.8)
        max_lat_accel = rospy.get_param('~max_lat_accel', 3.)
        max_steer_angle = rospy.get_param('~max_steer_angle', 8.)
        rate = rospy.get_param('~rate',50.)

        self.steer_pub = rospy.Publisher('/vehicle/steering_cmd',
                                         SteeringCmd, queue_size=1)
        self.throttle_pub = rospy.Publisher('/vehicle/throttle_cmd',
                                            ThrottleCmd, queue_size=1)
        self.brake_pub = rospy.Publisher('/vehicle/brake_cmd',
                                         BrakeCmd, queue_size=1)

        self.rate = rate

        # Create `TwistController` object
        self.controller = Controller(
            wheel_base=wheel_base,
            steer_ratio=steer_ratio,
            min_speed=0.0,
            max_lat_accel=max_lat_accel,
            max_steer_angle=max_steer_angle,
            th_kp=1.0,
            th_ki=0.0,
            th_kd=0.0,
            th_mn=0.0,
            th_mx=1.0,
            br_kp=(vehicle_mass+(GAS_DENSITY*fuel_capacity))*wheel_radius,
            br_ki=0.0,
            br_kd=0.0,
            br_mn=0.0,
            br_mx=1.0, 
            rate=rate
            )
        self.target_velocity = TwistStamped()
        self.current_velocity = TwistStamped()
        self.is_enabled = True
        

        # Subscribe to all the topics you need to
        rospy.Subscriber('/dbw_enabled', Bool, self.dbw_enabled_cb)
        rospy.Subscriber('/current_velocity', TwistStamped, self.current_velocity_cb)
        rospy.Subscriber('/twist_cmd', TwistStamped, self.twist_cb)

        self.loop()

    def dbw_enabled_cb(self, is_enabled):
        self.is_enabled = is_enabled

    def current_velocity_cb(self, velocity):
        self.current_velocity = velocity

    def twist_cb(self, twist):
        self.target_velocity = twist

    def loop(self): 
        rate = rospy.Rate(self.rate) # 50Hz

        while not rospy.is_shutdown():
            # Get predicted throttle, brake, and steering using `twist_controller`
            if self.is_enabled:
                throttle, brake, steering = self.controller.control(self.current_velocity, self.target_velocity)
                self.publish(throttle, brake, steering)
            rate.sleep()

    def publish(self, throttle, brake, steer):
        tcmd = ThrottleCmd()
        tcmd.enable = True
        tcmd.pedal_cmd_type = ThrottleCmd.CMD_PERCENT
        tcmd.pedal_cmd = throttle
        self.throttle_pub.publish(tcmd)

        scmd = SteeringCmd()
        scmd.enable = True
        scmd.steering_wheel_angle_cmd = steer
        self.steer_pub.publish(scmd)

        bcmd = BrakeCmd()
        bcmd.enable = True
        bcmd.pedal_cmd_type = BrakeCmd.CMD_TORQUE
        bcmd.pedal_cmd = brake
        self.brake_pub.publish(bcmd)


if __name__ == '__main__':
    DBWNode()
