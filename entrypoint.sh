#!/bin/bash
set -e

if [ -n "${DISPLAY:-}" ]; then
    export QT_QPA_PLATFORM=xcb
else
    export QT_QPA_PLATFORM=offscreen
fi

# Muda para a pasta de trabalho e carrega o ROS global
cd /usv_ws
source /opt/ros/jazzy/setup.bash

# Compila a área de trabalho ROS2 se o código não estiver compilado
if [ ! -d "install" ]; then
    echo "Código não compilado encontrado. Rodando 'colcon build'..."
    colcon build
fi

# Dá source na área de trabalho ROS2 específica apenas se existir
if [ -f /usv_ws/install/setup.bash ]; then
    source /usv_ws/install/setup.bash
else
    echo "Aviso: Workspace ROS 2 não encontrado ou não compilado em /usv_ws"
fi


# Abre a cena do CoppeliaSim
echo "Iniciando o CoppeliaSim em segundo plano..."
COPPELIASIM_BIN=$(find /opt -maxdepth 2 -name coppeliaSim.sh -type f | head -n 1)
if [ -z "$COPPELIASIM_BIN" ]; then
    echo "Erro: CoppeliaSim não encontrado em /opt."
    exit 1
fi

if [ -n "${DISPLAY:-}" ]; then
    echo "DISPLAY detectado em ${DISPLAY}. Iniciando CoppeliaSim com X11."
else
    echo "DISPLAY não detectado. Iniciando CoppeliaSim em modo headless."
fi

"$COPPELIASIM_BIN" /opt/cenas/cena_usv.ttt > /tmp/coppeliasim.log 2>&1 &
COPPELIASIM_PID=$!

sleep 5
if ! kill -0 "$COPPELIASIM_PID" 2>/dev/null; then
    echo "Erro: CoppeliaSim encerrou durante a inicialização."
    cat /tmp/coppeliasim.log
    exit 1
fi

echo "Aguardando 15 segundos para o CoppeliaSim terminar de subir..."
sleep 15

# Executa o arquivo de inicialização do ROS2
echo "Iniciando os nós do ROS 2..."
ros2 launch robot_bringup sim_launch.xml

# Mantém o terminal aberto
exec "$@"