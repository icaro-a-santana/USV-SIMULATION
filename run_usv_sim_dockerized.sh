#!/bin/bash
set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-simulacao_usv:latest}"
CONTAINER_NAME="${CONTAINER_NAME:-meu_container_usv_x11}"

# If a tar with the image is present in the current folder, load it and
# try to automatically determine the repository:tag to use.
TAR_FILE="simulacao_usv_image.tar"
if [ -f "$TAR_FILE" ]; then
    echo "Encontrado $TAR_FILE — carregando imagem Docker..."
    before_images=$(docker images --format "{{.Repository}}:{{.Tag}} {{.ID}}" || true)
    load_output=$(docker load -i "$TAR_FILE" 2>&1) || { echo "Falha ao executar 'docker load'"; echo "$load_output"; exit 1; }
    echo "$load_output"

    # Tentar extrair 'repository:tag' diretamente da saída do docker load
    loaded=$(printf "%s\n" "$load_output" | awk -F": " '/Loaded image: /{print $2; exit}')
    if [ -n "$loaded" ]; then
        IMAGE_NAME="$loaded"
        echo "Imagem carregada: $IMAGE_NAME"
    else
        # comparar listas de imagens antes/depois para identificar a nova imagem
        after_images=$(docker images --format "{{.Repository}}:{{.Tag}} {{.ID}}")
        new_entry=$(comm -13 <(printf "%s\n" "$before_images" | sort) <(printf "%s\n" "$after_images" | sort) | head -n1)
        image_candidate=$(printf "%s" "$new_entry" | awk '{print $1}') || true
        if [ -n "$image_candidate" ]; then
            IMAGE_NAME="$image_candidate"
            echo "Imagem detectada: $IMAGE_NAME"
        else
            echo "Não foi possível identificar automaticamente a tag da imagem. Usando: $IMAGE_NAME"
        fi
    fi
fi

if [ -z "${DISPLAY:-}" ]; then
    echo "DISPLAY não está definido no host. Este script é para uso com X11."
    exit 1
fi

xhost +si:localuser:root >/dev/null 2>&1 || true
trap 'xhost -si:localuser:root >/dev/null 2>&1 || true' EXIT

DOCKER_ARGS=(
    -it
    --rm
    --name "$CONTAINER_NAME"
    --env "DISPLAY=$DISPLAY"
    --env "QT_X11_NO_MITSHM=1"
    --volume "/tmp/.X11-unix:/tmp/.X11-unix:rw"
    --net=host
    --ipc=host
    --device /dev/dri
    --group-add video
)

if [ -n "${XAUTHORITY:-}" ] && [ -f "${XAUTHORITY}" ]; then
    DOCKER_ARGS+=(
        --env "XAUTHORITY=/root/.Xauthority"
        --volume "$XAUTHORITY:/root/.Xauthority:ro"
    )
fi

exec docker run "${DOCKER_ARGS[@]}" "$IMAGE_NAME"