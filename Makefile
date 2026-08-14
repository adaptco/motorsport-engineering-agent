.PHONY: test build-images build-images-v38

VERSION ?= 3.8

test:
	uv run --extra dev pytest -q

build-images:
	docker build --target control_plane -t mea-control-plane:$(VERSION) .
	docker build --target mcp_server -t mea-mcp-server:$(VERSION) .
	docker build --target worker -t mea-worker:$(VERSION) .

build-images-v38: VERSION=3.8
build-images-v38: build-images
