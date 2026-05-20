#!/usr/bin/env python3
# Converts /cmd_vel (Twist) to individual thruster commands, simulating a
# single motor + rudder boat: linear.x → same thrust on both motors,
# angular.z → same steering angle on both motors.

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import Float64


class CmdVelToThrusters(Node):

    def __init__(self):
        super().__init__('cmd_vel_to_thrusters')

        # max_thrust: thrust in Newtons corresponding to linear.x = 1.0
        # max_angle: thruster angle in radians corresponding to angular.z = 1.0
        self.declare_parameter('max_thrust', 1500.0)
        self.declare_parameter('max_angle', 0.5)

        self.max_thrust = self.get_parameter('max_thrust').value
        self.max_angle = self.get_parameter('max_angle').value

        self.left_thrust_pub = self.create_publisher(Float64, 'thrusters/left/thrust', 10)
        self.right_thrust_pub = self.create_publisher(Float64, 'thrusters/right/thrust', 10)
        self.left_pos_pub = self.create_publisher(Float64, 'thrusters/left/pos', 10)
        self.right_pos_pub = self.create_publisher(Float64, 'thrusters/right/pos', 10)

        self.create_subscription(Twist, 'cmd_vel', self._on_cmd_vel, 10)

    def _on_cmd_vel(self, msg):
        thrust = msg.linear.x * self.max_thrust
        # angular.z > 0 = turn left: motors angle positive pushes stern right → turns left
        angle = msg.angular.z * self.max_angle

        t_msg = Float64()
        t_msg.data = thrust
        self.left_thrust_pub.publish(t_msg)
        self.right_thrust_pub.publish(t_msg)

        a_msg = Float64()
        a_msg.data = angle
        self.left_pos_pub.publish(a_msg)
        self.right_pos_pub.publish(a_msg)


def main(args=None):
    rclpy.init(args=args)
    node = CmdVelToThrusters()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
