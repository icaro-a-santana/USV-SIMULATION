import rclpy
from rclpy.node import Node
from coppeliasim_zmqremoteapi_client import RemoteAPIClient
from std_msgs.msg import Float64
from cba_art_intrf.msg import NavDat

class Com(Node):
    
    def __init__(self, node_name: str = 'node'):
        super().__init__(node_name)

        # Comunicação com CoppeliaSim
        self.client = RemoteAPIClient(port=23000)
        self.sim = self.client.require('sim')
        self.client.setStepping(True)
        self.sim.startSimulation()
        self.log_sent = 0
    

        #Definição de frequencia de envio de informações
        self.iara = self.sim.getObject('/iara')
        self.t = 0.0
        self.t_increment = 0.1
        self.step_interval = 0.02
        self.total_force = 3
        self.f1_command = 0.0
        self.has_ctrl_msg = False

        # Estados anteriores para derivadas numericas de aceleracao
        self.prev_vx = 0.0
        self.prev_vy = 0.0
        self.prev_vyaw = 0.0
        self.has_prev_velocity = False
        
        # Timer para controlar o intervalo de step da simulação
        self.step_timer = self.create_timer(self.step_interval, self.step_simulation)

        # Receber sinais de controle do controller
        self.ctrl_subscriber_ = self.create_subscription(
            Float64, 'ctrl_sgn', self.callback_control_signal, 10
        )

        # Publicar Estado do barco no Topico "act_state"
        self.publisher_ = self.create_publisher(NavDat, "act_state", 10)
        
        # Nenhum log de inicializacao para manter apenas os sinais solicitados.

    def _get_current_pose(self):
        position = self.sim.getObjectPosition(self.iara, -1)
        orientation = self.sim.getObjectOrientation(self.iara, -1)
        return position, orientation

    def step_simulation(self):
        # Obter posição e orientação diretamente das APIs do CoppeliaSim.
        position, orientation = self._get_current_pose()
        
        state_msg = NavDat()
        state_msg.time = self.t
        state_msg.px = position[0]
        state_msg.py = position[1]

        # Sinais recebidos
        px = state_msg.px
        py = state_msg.py
        pyaw = orientation[2]
        dt = self.t_increment

        linear_velocity, angular_velocity = self.sim.getObjectVelocity(self.iara)
        vx = linear_velocity[0]
        vy = linear_velocity[1]
        vyaw = angular_velocity[2]

        if not self.has_prev_velocity:
            ax = 0.0
            ay = 0.0
            ayax = 0.0
            self.has_prev_velocity = True
        else:
            ax = (vx - self.prev_vx) / dt
            ay = (vy - self.prev_vy) / dt
            ayax = (vyaw - self.prev_vyaw) / dt

        state_msg.vy = vy
        state_msg.vx = vx
        state_msg.ax = ax
        state_msg.ay = ay
        state_msg.pyaw = pyaw
        state_msg.vyaw = vyaw
        state_msg.ayax = ayax

        # Publicar as informacoes para o topico
        self.publisher_.publish(state_msg)

        self.prev_vx = vx
        self.prev_vy = vy
        self.prev_vyaw = vyaw

        f1 = 0.0
        f2 = self.total_force

        # Nao aplica forca ate receber o primeiro comando em /ctrl_sgn.
        if not self.has_ctrl_msg:
            if self.log_sent == 0:
                self.get_logger().info('Aguardando comando de controle em /ctrl_sgn...')
                self.log_sent = 1
            self.client.step()
            self.t += self.t_increment
            
            return


        # Aplica duas forcas no referencial local do barco.
        # F1 vem de ctrl_sgn e F2 = F - F1, com pontos simetricos no eixo x.
        f1 = max(0.0, min(float(self.f1_command), self.total_force))
        f2 = self.total_force - f1

        point_1 = [0.2, 0.3, 0.0]
        point_2 = [-0.2, 0.3, 0.0]
        force_1 = [0.0, f1, 0.0]
        force_2 = [0.0, f2, 0.0]

        # Algumas versoes expoem objectHandleAddForce; outras expoem addForce.
        if hasattr(self.sim, 'objectHandleAddForce'):
            self.sim.objectHandleAddForce(self.iara, point_1, force_1)
            self.sim.objectHandleAddForce(self.iara, point_2, force_2)
        else:
            self.sim.addForce(self.iara, point_1, force_1)
            self.sim.addForce(self.iara, point_2, force_2)

        # Avance um passo na simulacao
        self.client.step()
        self.t += self.t_increment


    def callback_control_signal(self, msg: Float64):
        self.f1_command = float(msg.data)
        self.has_ctrl_msg = True

def main(args=None): #Rotina Principal
    rclpy.init(args=args)
    node = Com("coppelia_com_node") # Nomeia e inicia o nó
    rclpy.spin(node) # Faz o nó continuar processando callbacks
    rclpy.shutdown() # Encerra o nó

if __name__ == '__main__': # Somente executa se for o arquivo principal
    main()
