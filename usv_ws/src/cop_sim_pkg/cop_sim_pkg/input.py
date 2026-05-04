import threading
import time
import rclpy
from rclpy.node import Node
from cba_art_intrf.srv import Trajectory


class InputNode(Node):

    def __init__(self, node_name: str = 'input_node'):
        super().__init__(node_name)

        # Cria o cliente e aguarda a conexão com o servidor
        self.client = self.create_client(Trajectory, 'trajectory')
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Aguardando serviço trajectory...')

        #Recebe os pontos da trajetória via terminal
        self.get_logger().info('Input node iniciado. Informe vetores 3D no terminal.')

        self._input_thread = threading.Thread(target=self._terminal_flow, daemon=True) #chama funcao terminal_flow como callback
        self._input_thread.start()

    def _terminal_flow(self): # Estabelece ciclo de dados do terminal
        while True:
            try: #Recebe valores de posição da trajetoria
                x_value = float(input('Digite x: ').strip())
                y_value = float(input('Digite y: ').strip())
                z_value = float(input('Digite z: ').strip())
            except ValueError: # Tratamento de erro para entradas
                print('Entrada invalida. Digite valores numericos para x, y e z.')
                continue
            except EOFError:
                print('Entrada encerrada.')
                return

            # Cria request e envia os dados de posição para o controlador
            request = Trajectory.Request() 
            request.target.x = x_value
            request.target.y = y_value
            request.target.z = z_value

            # Espera a trajetória ser concluída e Sinaliza
            completed = self._call_trajectory(request)
            while rclpy.ok() and not completed:
                print('Trajetoria em andamento... aguardando finalizacao.')
                time.sleep(1.0)
                completed = self._call_trajectory(request)

            print('Trajetoria concluida para esse ponto.')

            # Pergunta se deseja adicionar mais pontos para serem seguidos
            add_more = input('Deseja adicionar mais pontos? (s/n): ').strip().lower()
            if add_more not in {'s', 'sim', 'y', 'yes'}:
                break

        rclpy.shutdown()

    
    def _call_trajectory(self, request: Trajectory.Request) -> bool: #
        future = self.client.call_async(request)
        while rclpy.ok() and not future.done():
            time.sleep(0.05)

        if future.result() is None:
            self.get_logger().error('Falha na chamada do servico trajectory.')
            return False

        return future.result().completed


def main(args=None): # Código Principal
    rclpy.init(args=args)
    node = InputNode('input_node')
    rclpy.spin(node)


if __name__ == '__main__': #Só executa se for o arquivo principal
    main()

