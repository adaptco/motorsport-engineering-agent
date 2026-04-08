.PHONY: cfd-api-install cfd-api-run cfd-api-test cfd-web-install cfd-web-run cfd-web-build cfd-stack-up cfd-stack-down

CFD_ROOT=packages/cfd-multimodal-agent
CFD_API=$(CFD_ROOT)/apps/api
CFD_WEB=$(CFD_ROOT)/apps/web

cfd-api-install:
	cd $(CFD_API) && python -m pip install -e .[dev]

cfd-api-run:
	cd $(CFD_API) && uvicorn cfd_api.main:app --reload --port 8000

cfd-api-test:
	cd $(CFD_API) && pytest

cfd-web-install:
	cd $(CFD_WEB) && npm install

cfd-web-run:
	cd $(CFD_WEB) && npm run dev

cfd-web-build:
	cd $(CFD_WEB) && npm run build

cfd-stack-up:
	docker compose -f docker-compose.v3_8.yml up --build

cfd-stack-down:
	docker compose -f docker-compose.v3_8.yml down
