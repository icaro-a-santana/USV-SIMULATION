FROM osrf/ros:jazzy-desktop

ENV DEBIAN_FRONTEND=noninteractive

ENV COPPELIASIM_HOME=/opt/CoppeliaSim



# Atualiza o sistema e instala dependências para interface gráfica, áudio e utilitários
RUN apt-get update && apt-get install -y --no-install-recommends \
        wget \
        ca-certificates \
        x11-xserver-utils \
        xauth \
        xvfb \
        libgl1-mesa-dri \
        libgl1 \
        libxrandr2 \
        libxinerama1 \
        libxcursor1 \
        libxss1 \
        libasound2t64 \
        pulseaudio \
        python3-pip \
        unzip \
        && rm -rf /var/lib/apt/lists/*

WORKDIR /opt

# Cria cena do CoppeliaSim dentro do container
RUN mkdir -p /opt/cenas
COPY ./cena_usv.ttt /opt/cenas/

# Copia a instalação local do CoppeliaSim para dentro da imagem
COPY CoppeliaSim/ ${COPPELIASIM_HOME}/
RUN python3 -m pip install --break-system-packages --no-cache-dir ${COPPELIASIM_HOME}/programming/zmqRemoteApi/clients/python
COPY usv_ws /usv_ws
COPY entrypoint.sh /entrypoint.sh

# Dá permissão de execução ao script
RUN chmod +x /entrypoint.sh

# Faz o source do ROS global e do workspace automaticamente em shells bash no container.
RUN printf '%s\n' \
                '#!/bin/bash' \
                'source /opt/ros/jazzy/setup.bash' \
                'if [ -f /usv_ws/install/setup.bash ]; then' \
                '  source /usv_ws/install/setup.bash' \
                'fi' \
                > /etc/profile.d/usv_ros_setup.sh && \
        chmod +x /etc/profile.d/usv_ros_setup.sh && \
        printf '%s\n' 'source /etc/profile.d/usv_ros_setup.sh' >> /root/.bashrc && \
        printf '%s\n' 'source /etc/profile.d/usv_ros_setup.sh' >> /etc/bash.bashrc



# Adiciona o CoppeliaSim ao PATH do sistema
ENV PATH="${COPPELIASIM_HOME}:$PATH"
ENV QT_X11_NO_MITSHM=1

# Define o script como ponto de entrada padrão
ENTRYPOINT ["/entrypoint.sh"]

SHELL ["/bin/bash", "-c"]

CMD ["bash"]