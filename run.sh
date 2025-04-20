#!/bin/bash
# Script to build and run the NiFi exporter Docker container

# Default values
NIFI_URL="http://nifi-hostname:8080"
PORT=9100
CONTAINER_NAME="nifi-exporter"
IMAGE_NAME="nifi-exporter"

# Display help message
function show_help {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  -h, --help                 Show this help message"
    echo "  -u, --url URL              NiFi URL (default: $NIFI_URL)"
    echo "  -p, --port PORT            Port to expose metrics on (default: $PORT)"
    echo "  -n, --name NAME            Container name (default: $CONTAINER_NAME)"
    echo "  -i, --image NAME           Image name (default: $IMAGE_NAME)"
    echo "  -b, --build-only           Build the Docker image but don't run it"
    echo "  -r, --run-only             Run the container without building the image"
    echo ""
    echo "Example:"
    echo "  $0 --url http://nifi-host:8080 --port 9101"
    exit 0
}

# Parse command line arguments
BUILD=true
RUN=true

while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -h|--help)
            show_help
            ;;
        -u|--url)
            NIFI_URL="$2"
            shift
            shift
            ;;
        -p|--port)
            PORT="$2"
            shift
            shift
            ;;
        -n|--name)
            CONTAINER_NAME="$2"
            shift
            shift
            ;;
        -i|--image)
            IMAGE_NAME="$2"
            shift
            shift
            ;;
        -b|--build-only)
            RUN=false
            shift
            ;;
        -r|--run-only)
            BUILD=false
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            ;;
    esac
done

# Build the Docker image
if [ "$BUILD" = true ]; then
    echo "Building Docker image: $IMAGE_NAME"
    docker build -t $IMAGE_NAME .
    
    if [ $? -ne 0 ]; then
        echo "Error: Failed to build Docker image"
        exit 1
    fi
    
    echo "Docker image built successfully"
fi

# Run the Docker container
if [ "$RUN" = true ]; then
    # Check if container already exists
    if docker ps -a | grep -q $CONTAINER_NAME; then
        echo "Container $CONTAINER_NAME already exists, removing it"
        docker rm -f $CONTAINER_NAME
    fi
    
    echo "Running Docker container: $CONTAINER_NAME"
    echo "NiFi URL: $NIFI_URL"
    echo "Exposing metrics on port: $PORT"
    
    docker run -d \
        --name $CONTAINER_NAME \
        -p $PORT:9100 \
        -e NIFI_URL=$NIFI_URL \
        $IMAGE_NAME
    
    if [ $? -ne 0 ]; then
        echo "Error: Failed to run Docker container"
        exit 1
    fi
    
    echo "Docker container started successfully"
    echo "Metrics available at: http://localhost:$PORT/metrics"
fi

exit 0
