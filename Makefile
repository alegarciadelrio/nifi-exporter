# Makefile for NiFi Exporter

.PHONY: build run stop clean test docker-build docker-run docker-stop docker-clean help

# Default values
NIFI_URL ?= http://nifi-hostname:8080
PORT ?= 9100
CONTAINER_NAME ?= nifi-exporter
IMAGE_NAME ?= nifi-exporter

# Help command
help:
	@echo "NiFi Exporter Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make [command]"
	@echo ""
	@echo "Commands:"
	@echo "  build              Install Python dependencies"
	@echo "  run                Run the exporter locally"
	@echo "  test               Run the test script"
	@echo "  docker-build       Build the Docker image"
	@echo "  docker-run         Run the Docker container"
	@echo "  docker-stop        Stop the Docker container"
	@echo "  docker-clean       Remove the Docker container and image"
	@echo "  clean              Remove Python cache files"
	@echo "  help               Show this help message"
	@echo ""
	@echo "Environment variables:"
	@echo "  NIFI_URL           NiFi URL (default: $(NIFI_URL))"
	@echo "  PORT               Port to expose metrics on (default: $(PORT))"
	@echo "  CONTAINER_NAME     Container name (default: $(CONTAINER_NAME))"
	@echo "  IMAGE_NAME         Image name (default: $(IMAGE_NAME))"

# Local development commands
build:
	pip install -r requirements.txt

run:
	NIFI_URL=$(NIFI_URL) python nifi_exporter.py

test:
	python test_exporter.py localhost $(PORT)

clean:
	rm -rf __pycache__
	rm -rf *.pyc

# Docker commands
docker-build:
	docker build -t $(IMAGE_NAME) .

docker-run:
	@if docker ps -a | grep -q $(CONTAINER_NAME); then \
		echo "Container $(CONTAINER_NAME) already exists, removing it"; \
		docker rm -f $(CONTAINER_NAME); \
	fi
	docker run -d --name $(CONTAINER_NAME) -p $(PORT):9100 -e NIFI_URL=$(NIFI_URL) $(IMAGE_NAME)
	@echo "Container started. Metrics available at: http://localhost:$(PORT)/metrics"

docker-stop:
	docker stop $(CONTAINER_NAME)

docker-clean: docker-stop
	docker rm $(CONTAINER_NAME)
	docker rmi $(IMAGE_NAME)

# Default target
.DEFAULT_GOAL := help
