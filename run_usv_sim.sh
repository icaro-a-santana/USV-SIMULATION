#!/bin/bash
set -e

if [ -z "${DISPLAY:-}" ]; then
     echo "DISPLAY não está definido no host. O container vai subir em modo headless."
else
     xhost +si:localuser:root >/dev/null 2>&1 || true
     trap 'xhost -si:localuser:root >/dev/null 2>&1 || true' EXIT
fi

XAUTHORITY_VOLUME=()
if [ -n "${XAUTHORITY:-}" ] && [ -f "${XAUTHORITY}" ]; then
     XAUTHORITY_VOLUME=(--volume="${XAUTHORITY}:/root/.Xauthority:ro" --env="XAUTHORITY=/root/.Xauthority")
fi

docker run -it --rm \
      --env="DISPLAY=${DISPLAY:-}" \
     --env="QT_X11_NO_MITSHM=1" \
     --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
      "${XAUTHORITY_VOLUME[@]}" \
     --volume="$(pwd)/usv_ws:/usv_ws:rw" \
     --net=host \
     --ipc=host \
     --name meu_container_usv \
     simulacao_usv:latest