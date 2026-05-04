import math
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64

from cba_art_intrf.msg import NavDat
from cba_art_intrf.srv import Trajectory


class Controler(Node):

    def __init__(self):
        super().__init__('control_node')

        # ESTADO
        self.boat_x = 0.0
        self.boat_y = 0.0
        self.boat_yaw = 0.0
        self.prev_error = 0.0
        self.state_received = False

        # CONTROLE
        self.max_force = 2.0
        self.control_force = 0.0

        # GANHOS
        self.kp = 0.6
        self.kd = 3.5
        self.kr = 1.2   # NOVO: anti-rotação contínua

        self.e_switch = 0.2

        # VELOCIDADE ANGULAR
        self.prev_yaw = 0.0
        self.omega_filtered = 0.0
        self.alpha_filter = 0.15

        # TRAJETÓRIA
        self.target_position = None
        self.reach_tolerance = 0.05

        # ROS
        self.sub = self.create_subscription(
            NavDat, 'act_state', self.callback_act_state, 10
        )

        self.pub = self.create_publisher(
            Float64, 'ctrl_sgn', 10
        )

        self.srv = self.create_service(
            Trajectory, 'trajectory', self.handle_trajectory_request
        )

        self.dt = 0.01
        self.timer = self.create_timer(self.dt, self.control_loop)

    def callback_act_state(self, msg):
        self.boat_x = msg.px
        self.boat_y = msg.py
        self.boat_yaw = msg.pyaw
        self.state_received = True

    def handle_trajectory_request(self, request, response):
        self.target_position = [request.target.x, request.target.y]
        response.completed = self.is_trajectory_completed()
        return response

    def is_trajectory_completed(self):
        if self.target_position is None or not self.state_received:
            return False

        dx = self.target_position[0] - self.boat_x
        dy = self.target_position[1] - self.boat_y

        return math.sqrt(dx*dx + dy*dy) <= self.reach_tolerance

    def wrap_angle(self, angle):
        return math.atan2(math.sin(angle), math.cos(angle))

    def wrap_angle_continuous(self, angle, prev_angle):
        delta = math.atan2(math.sin(angle - prev_angle), math.cos(angle - prev_angle))
        return prev_angle + delta

    def saturate(self, value, vmin, vmax):
        return max(vmin, min(value, vmax))

    def publish(self, value):
        msg = Float64()
        msg.data = float(value)
        self.pub.publish(msg)

    def control_loop(self):

        if not self.state_received or self.target_position is None:
            return

        # VELOCIDADE ANGULAR
        raw_omega = (self.boat_yaw - self.prev_yaw) / self.dt
        self.prev_yaw = self.boat_yaw

        self.omega_filtered = (
            self.alpha_filter * raw_omega +
            (1 - self.alpha_filter) * self.omega_filtered
        )

        # PARADA
        if self.is_trajectory_completed():
            self.publish(0.0)
            return

        # REFERÊNCIA
        dx = self.target_position[0] - self.boat_x
        dy = self.target_position[1] - self.boat_y
        theta_ref = math.atan2(dy, dx)

        # ERRO CONTÍNUO
        raw_error = self.wrap_angle(theta_ref - self.boat_yaw)
        error = self.wrap_angle_continuous(raw_error, self.prev_error)

        # CONTROLE BASE
        if abs(error) < self.e_switch:
            u = self.kp * error - self.kd * self.omega_filtered
        else:
            u = self.kp * math.sin(error) - self.kd * self.omega_filtered

        # ANTI-SPIN (FORÇA REVERSA)
        u -= self.kr * math.copysign(abs(self.omega_filtered), self.omega_filtered)

        # DETECÇÃO DE PASSAGEM PELO ALVO
        if error * self.prev_error < 0:
            u *= -0.5  # inverte e reduz

        # SATURAÇÃO
        self.control_force = self.saturate(u, -self.max_force, self.max_force)

        # DEAD-ZONE
        if abs(error) < 0.03 and abs(self.omega_filtered) < 0.08:
            self.control_force = 0.0

        self.prev_error = error

        self.publish(self.control_force)

        self.get_logger().info(
            f"CTRL | e:{error:.3f} | w:{self.omega_filtered:.3f} | F1:{self.control_force:.3f}"
        )


def main(args=None):
    rclpy.init(args=args)
    node = Controler()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()