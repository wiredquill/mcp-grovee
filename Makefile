.PHONY: help install build run test clean docker-build docker-run k8s-deploy k8s-delete

# Variables
PYTHON := python3
VENV := venv
DOCKER_IMAGE := mcp-govee
DOCKER_TAG := latest
K8S_NAMESPACE := mcp-govee

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies in virtual environment
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.txt

env: ## Create .env file from example
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env file. Please edit it with your Govee API key."; \
	else \
		echo ".env file already exists."; \
	fi

run: ## Run the MCP server locally
	$(VENV)/bin/python -m src.server

test: ## Run tests (placeholder)
	@echo "No tests defined yet"

clean: ## Clean up build artifacts
	rm -rf $(VENV)
	rm -rf src/__pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

docker-build: ## Build Docker image
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

docker-run: ## Run Docker container interactively
	docker run -i --rm --env-file .env $(DOCKER_IMAGE):$(DOCKER_TAG)

docker-push: ## Push Docker image to registry (update image name first)
	@echo "Update image name in Makefile before pushing"
	# docker push your-registry.com/$(DOCKER_IMAGE):$(DOCKER_TAG)

k8s-deploy: ## Deploy to Kubernetes
	kubectl apply -k k8s/

k8s-delete: ## Delete from Kubernetes
	kubectl delete -k k8s/

k8s-logs: ## View Kubernetes logs
	kubectl logs -n $(K8S_NAMESPACE) deployment/mcp-govee-server -f

k8s-status: ## Check Kubernetes deployment status
	kubectl get all -n $(K8S_NAMESPACE)

lint: ## Run linting (requires black and flake8)
	@if [ -d $(VENV) ]; then \
		$(VENV)/bin/black --check src/; \
		$(VENV)/bin/flake8 src/; \
	else \
		echo "Virtual environment not found. Run 'make install' first."; \
	fi

format: ## Format code with black
	@if [ -d $(VENV) ]; then \
		$(VENV)/bin/black src/; \
	else \
		echo "Virtual environment not found. Run 'make install' first."; \
	fi
