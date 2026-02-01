#!/bin/bash
# Start vLLM servers using Docker (recommended for CUDA compatibility)

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ============================================
# Docker Permission Check
# ============================================
# Check if we can access Docker. If not, try to use the docker group.
check_docker_access() {
    # Test if docker is accessible
    if docker info > /dev/null 2>&1; then
        return 0  # Docker is accessible
    fi
    
    # Docker not accessible - check if user is in docker group (in /etc/group)
    if grep -q "^docker:.*:.*${USER}" /etc/group 2>/dev/null; then
        # User is in docker group but current session doesn't have it
        # Check if we're already trying to use sg (prevent infinite loop)
        if [ "${DOCKER_GROUP_RETRY:-}" = "1" ]; then
            echo -e "${RED}Error: Still cannot access Docker after group switch.${NC}"
            echo "Try logging out and back in, or run: newgrp docker"
            exit 1
        fi
        
        echo -e "${YELLOW}Docker group not active in current session. Activating...${NC}"
        # Re-execute this script with the docker group
        export DOCKER_GROUP_RETRY=1
        exec sg docker -c "\"$0\" $*"
    else
        # User is not in docker group at all
        echo -e "${RED}Error: Cannot access Docker.${NC}"
        echo ""
        echo "You are not in the 'docker' group. To fix this:"
        echo "  1. Add yourself to the docker group:"
        echo "     sudo usermod -aG docker \$USER"
        echo "  2. Log out and log back in (or run: newgrp docker)"
        echo ""
        echo "Alternatively, run this script with sudo."
        exit 1
    fi
}

# Run the docker access check
check_docker_access "$@"

# Default to single model
COMPOSE_FILE="docker-compose-single.yml"
MODE="single"

show_help() {
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}  vLLM Docker Server Manager${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    echo "Usage:"
    echo "  $0 start [single|dual]  Start model server(s)"
    echo "  $0 stop                 Stop all servers"
    echo "  $0 status               Show server status"
    echo "  $0 logs [container]     Show logs (follow mode)"
    echo "  $0 pull                 Pull latest vLLM image"
    echo ""
    echo "Modes:"
    echo "  single  - Run one 70B model (Llama 3.3 70B NVFP4) on port 8000"
    echo "  dual    - Run two medium models (Mistral 24B + Qwen3 32B) on ports 8000/8001"
    echo ""
    echo "Examples:"
    echo "  $0 start single    # Start single 70B model"
    echo "  $0 start dual      # Start dual medium models"
    echo "  $0 logs            # Follow all logs"
    echo "  $0 stop            # Stop all containers"
    echo ""
}

set_mode() {
    case "${1:-single}" in
        single|s|1)
            COMPOSE_FILE="docker-compose-single.yml"
            MODE="single"
            ;;
        dual|d|2|medium)
            COMPOSE_FILE="docker-compose-dual-medium.yml"
            MODE="dual"
            ;;
        *)
            echo -e "${RED}Unknown mode: $1${NC}"
            echo "Use 'single' or 'dual'"
            exit 1
            ;;
    esac
}

start_servers() {
    set_mode "${1:-single}"
    
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}  Starting vLLM Docker Server(s)${NC}"
    echo -e "${GREEN}  Mode: ${MODE}${NC}"
    echo -e "${GREEN}  (NVIDIA Container with CUDA 13.1)${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    
    # Check if other containers are running
    if docker ps --format '{{.Names}}' | grep -q "vllm-"; then
        echo -e "${YELLOW}Stopping existing vLLM containers...${NC}"
        docker compose -f docker-compose-single.yml down 2>/dev/null || true
        docker compose -f docker-compose-dual-medium.yml down 2>/dev/null || true
        echo ""
    fi
    
    echo -e "${CYAN}Pulling NVIDIA vLLM image (CUDA 13.1)...${NC}"
    docker pull nvcr.io/nvidia/vllm:25.12-py3
    echo ""
    
    if [ "$MODE" = "dual" ]; then
        # Sequential startup for dual mode to avoid memory contention
        echo -e "${CYAN}Starting Mistral-24B first (sequential startup for memory)...${NC}"
        docker compose -f "$COMPOSE_FILE" up -d mistral-24b
        echo ""
        
        echo -e "${YELLOW}Waiting for Mistral to be ready (this takes 2-3 minutes)...${NC}"
        ATTEMPTS=0
        MAX_ATTEMPTS=30
        while ! curl -s http://localhost:8000/health > /dev/null 2>&1; do
            ATTEMPTS=$((ATTEMPTS + 1))
            if [ $ATTEMPTS -ge $MAX_ATTEMPTS ]; then
                echo -e "${RED}Mistral did not start in time. Check logs with: $0 logs vllm-mistral-24b${NC}"
                exit 1
            fi
            echo "  Check $ATTEMPTS/$MAX_ATTEMPTS: Still loading..."
            sleep 15
        done
        echo -e "${GREEN}Mistral is ready!${NC}"
        echo ""
        
        echo -e "${CYAN}Starting Qwen3-32B (second model)...${NC}"
        docker compose -f "$COMPOSE_FILE" up -d qwen3-32b
        echo ""
        
        echo -e "${YELLOW}Waiting for Qwen3 to be ready (this takes 2-3 minutes)...${NC}"
        ATTEMPTS=0
        while ! curl -s http://localhost:8001/health > /dev/null 2>&1; do
            ATTEMPTS=$((ATTEMPTS + 1))
            if [ $ATTEMPTS -ge $MAX_ATTEMPTS ]; then
                echo -e "${RED}Qwen3 did not start in time. Check logs with: $0 logs vllm-qwen3-32b${NC}"
                exit 1
            fi
            echo "  Check $ATTEMPTS/$MAX_ATTEMPTS: Still loading..."
            sleep 15
        done
        echo -e "${GREEN}Qwen3 is ready!${NC}"
    else
        # Single mode - just start normally
        echo -e "${CYAN}Starting server with ${COMPOSE_FILE}...${NC}"
        docker compose -f "$COMPOSE_FILE" up -d
    fi
    echo ""
    
    if [ "$MODE" = "single" ]; then
        echo -e "${GREEN}Server starting!${NC}"
        echo ""
        echo "Model: Llama 3.3 70B NVFP4 (~40 GB download)"
        echo ""
        echo "Endpoint:"
        echo "  - Llama 70B: http://localhost:8000"
        echo ""
        echo "Commands:"
        echo "  $0 status  - Check if server is ready"
        echo "  $0 logs    - View download/startup progress"
        echo "  $0 stop    - Stop server"
    else
        echo -e "${GREEN}============================================${NC}"
        echo -e "${GREEN}  Both models are ready!${NC}"
        echo -e "${GREEN}============================================${NC}"
        echo ""
        echo "Models: Mistral-Small 24B + Qwen3 32B (both NVFP4)"
        echo ""
        echo "Endpoints:"
        echo "  - Mistral 24B (Mistral AI): http://localhost:8000"
        echo "  - Qwen3 32B (Alibaba):      http://localhost:8001"
        echo ""
        echo "Memory Usage:"
        echo "  - Mistral: ~15 GB weights + ~18 GB KV cache"
        echo "  - Qwen3:   ~20 GB weights + ~20 GB KV cache"
        echo ""
        echo "Commands:"
        echo "  $0 status  - Check server status"
        echo "  $0 logs    - View logs"
        echo "  $0 stop    - Stop all servers"
    fi
}

stop_servers() {
    echo -e "${YELLOW}Stopping all vLLM servers...${NC}"
    docker compose -f docker-compose-single.yml down 2>/dev/null || true
    docker compose -f docker-compose-dual-medium.yml down 2>/dev/null || true
    echo -e "${GREEN}All servers stopped${NC}"
}

show_status() {
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}  vLLM Docker Server Status${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
    
    # Show running containers
    CONTAINERS=$(docker ps --filter "name=vllm-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null)
    if [ -n "$CONTAINERS" ]; then
        echo -e "${CYAN}Running Containers:${NC}"
        echo "$CONTAINERS"
    else
        echo -e "${YELLOW}No vLLM containers running${NC}"
        echo ""
        echo "Start with:"
        echo "  $0 start single   # Single 70B model"
        echo "  $0 start dual     # Two small models"
        return
    fi
    
    echo ""
    echo -e "${CYAN}Health Checks:${NC}"
    
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        MODEL=$(curl -s http://localhost:8000/v1/models 2>/dev/null | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4 || echo "unknown")
        echo -e "  Port 8000: ${GREEN}● Ready${NC} ($MODEL)"
    elif docker ps --format '{{.Names}}' | grep -q "vllm-.*8000\|vllm-llama"; then
        echo -e "  Port 8000: ${YELLOW}● Loading...${NC}"
    else
        echo -e "  Port 8000: ${RED}● Not running${NC}"
    fi
    
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        MODEL=$(curl -s http://localhost:8001/v1/models 2>/dev/null | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4 || echo "unknown")
        echo -e "  Port 8001: ${GREEN}● Ready${NC} ($MODEL)"
    elif docker ps --format '{{.Names}}' | grep -q "vllm-.*8001\|vllm-qwen"; then
        echo -e "  Port 8001: ${YELLOW}● Loading...${NC}"
    fi
    
    echo ""
    echo -e "${CYAN}GPU Memory:${NC}"
    GPU_INFO=$(nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null)
    if [ -n "$GPU_INFO" ] && ! echo "$GPU_INFO" | grep -q "N/A"; then
        # Parse numeric values (format: "used, total")
        USED=$(echo "$GPU_INFO" | cut -d',' -f1 | tr -d ' ')
        TOTAL=$(echo "$GPU_INFO" | cut -d',' -f2 | tr -d ' ')
        if [ "$TOTAL" -gt 0 ] 2>/dev/null; then
            USED_GB=$(echo "scale=2; $USED/1024" | bc)
            TOTAL_GB=$(echo "scale=2; $TOTAL/1024" | bc)
            PERCENT=$(echo "scale=1; ($USED/$TOTAL)*100" | bc)
            echo "  Used: ${USED_GB} GB / ${TOTAL_GB} GB (${PERCENT}%)"
        else
            echo "  DGX Spark: 128 GB unified memory (shared CPU/GPU)"
        fi
    elif echo "$GPU_INFO" | grep -q "N/A"; then
        # DGX Spark with unified memory shows N/A
        echo "  DGX Spark: 128 GB unified memory (shared CPU/GPU)"
    else
        echo "  Unable to query GPU (nvidia-smi not available)"
    fi
}

show_logs() {
    CONTAINER="${1:-}"
    
    if [ -n "$CONTAINER" ]; then
        echo -e "${CYAN}Following logs for $CONTAINER (Ctrl+C to exit)...${NC}"
        docker logs -f "$CONTAINER"
    else
        # Show logs for whichever compose file has running containers
        if docker ps --format '{{.Names}}' | grep -q "vllm-llama-70b"; then
            echo -e "${CYAN}Following logs (Ctrl+C to exit)...${NC}"
            docker compose -f docker-compose-single.yml logs -f
        elif docker ps --format '{{.Names}}' | grep -q "vllm-mistral\|vllm-qwen3"; then
            echo -e "${CYAN}Following logs (Ctrl+C to exit)...${NC}"
            docker compose -f docker-compose-dual-medium.yml logs -f
        else
            echo -e "${YELLOW}No vLLM containers running${NC}"
        fi
    fi
}

pull_image() {
    echo -e "${CYAN}Pulling NVIDIA vLLM image (CUDA 13.1)...${NC}"
    docker pull nvcr.io/nvidia/vllm:25.12-py3
    echo -e "${GREEN}Done!${NC}"
}

case "${1:-}" in
    start)
        start_servers "${2:-single}"
        ;;
    stop)
        stop_servers
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs "${2:-}"
        ;;
    pull)
        pull_image
        ;;
    *)
        show_help
        ;;
esac
