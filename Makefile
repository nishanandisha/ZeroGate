# ZeroGate - one-command workflows.  `make help`
DC = docker compose -f infrastructure/docker-compose.yml
S ?=

.PHONY: help init pki up down destroy ps logs test unit integration lint scenarios break diagnose fix verify cycle breakfix demo security

help:            ## Show this help
	@grep -E '^[a-z-]+:.*##' Makefile | awk -F':.*## ' '{printf "  %-12s %s\n", $$1, $$2}'
init:            ## Create infrastructure/.env, the PKI and the test virtualenv
	@test -f infrastructure/.env || cp .env.example infrastructure/.env
	@./scripts/pki.sh
	@test -d testing/.venv || (python3 -m venv testing/.venv && testing/.venv/bin/pip install -q -r testing/requirements.txt)
up: init         ## Build and start the whole lab
	$(DC) up -d --build
	@echo "Console http://localhost:3300 | App https://localhost:8443 | Keycloak http://localhost:8080 | API http://localhost:8800/api/docs"
down:            ## Stop the lab (keeps data)
	$(DC) down
destroy:         ## Stop the lab and delete its volumes
	$(DC) down -v
ps:              ## Container status
	$(DC) ps
logs:            ## Follow logs (S=service)
	$(DC) logs -f --tail 50 $(S)
unit:            ## Backend unit tests + lint
	cd backend && .venv/bin/python -m pytest -q && .venv/bin/ruff check app tests
integration:     ## Integration tests against the running lab
	cd testing && .venv/bin/python -m pytest
security:        ## Leak and exposure checks: repo contents, API auth, console (lab must be up)
	cd testing && .venv/bin/python -m pytest security -v
test: unit integration security  ## All tests
scenarios:       ## List break/fix scenarios
	@testing/break-fix/run.sh list
break diagnose fix verify cycle:  ## Run one step of a scenario, e.g. make break S=03
	@testing/break-fix/run.sh $@ $(S)
breakfix:        ## Cycle every scenario and write testing/reports/break-fix-report.md
	@testing/break-fix/run.sh all
demo:            ## Client-side demo: tunnel, segmentation, inspection
	$(DC) exec client-wg zg status
	$(DC) exec client-wg zg test
