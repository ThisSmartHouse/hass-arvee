#!/bin/bash

display_error() {
    echo -e "\033[0;31mERROR: $1\033[0m"
    echo "Terminal will close in 5 seconds..."
    sleep 5
    exit 1
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if ! cd "$PROJECT_ROOT"; then
    display_error "Failed to change to project root directory: $PROJECT_ROOT"
fi

if ! command -v docker &> /dev/null; then
    display_error "Docker is not installed or not in PATH"
fi

if ! docker info &> /dev/null; then
    display_error "Docker daemon is not running"
fi

echo "Starting aider in Docker container..."
if ! docker run -it --rm --user "$(id -u):$(id -g)" --volume "$PROJECT_ROOT:/app" --volume "$PROJECT_ROOT/../hass-arvee-k3vmcd:/k3vmcd" paulgauthier/aider-full; then
    display_error "Failed to run aider Docker container"
fi

echo "Aider session completed successfully."
