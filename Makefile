# Name of the container and image
IMAGE_NAME := janus
CONTAINER_NAME := janus
VERSION := $(shell git describe --always --abbrev=0)

# Default build target
.PHONY: build
build:
	podman build \
		--build-arg UID=$$(id -u) \
		--build-arg GID=$$(id -g) \
		--tag $(IMAGE_NAME):$(VERSION) \
		--tag $(IMAGE_NAME):latest \
		.

# Start the container detached (e.g. for background server)
# FIXME: git does not work in the container right now, not a big deal
.PHONY: up
up:
	-podman volume create $(CONTAINER_NAME)-bash-history
	-podman run -d \
		--name $(CONTAINER_NAME) \
		--hostname $(CONTAINER_NAME) \
		--userns keep-id \
		--volume $(CONTAINER_NAME)-bash-history:/home/ubuntu/bash_history \
		--volume ./:/home/ubuntu/repo/:z \
		--volume /app/.venv \
		--workdir /home/ubuntu/repo \
		$(IMAGE_NAME):latest

# Stop and remove a named container
.PHONY: down
down:
	-podman stop $(CONTAINER_NAME) --time 1
	-podman rm $(CONTAINER_NAME)

# Shell into the container (must already be running)
.PHONY: shell
shell:
	podman exec -it $(CONTAINER_NAME) bash

# Restart the container
.PHONY: restart
restart: down up
