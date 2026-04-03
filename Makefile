.PHONY: test build-images

test:
	pytest -q

build-images:
	docker build -t mea/control-plane:local -f control_plane/Dockerfile .
	docker build -t mea/mcp-server:local -f mcp_server/Dockerfile .
	docker build -t mea/worker:local -f worker/Dockerfile .
