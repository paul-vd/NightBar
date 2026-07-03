# NightBar task runner.  Think of these like package.json "scripts".
#   make          -> list commands
#   make run      -> run from source            (~ npm run dev)
#   make build    -> compile dist/NightBar.app  (~ npm run build)
#   make app      -> build then launch it
#   make clean    -> remove build output
# Every target auto-creates .venv and installs deps on first use, so a
# fresh clone just needs `make run`.

VENV  := .venv
PY    := $(VENV)/bin/python
PIP   := $(VENV)/bin/pip
STAMP := $(VENV)/.deps-installed

.DEFAULT_GOAL := help

# (Re)build the venv whenever requirements.txt changes.
$(STAMP): requirements.txt
	python3 -m venv $(VENV)
	$(PIP) install -q --upgrade pip
	$(PIP) install -q -r requirements.txt
	@touch $(STAMP)

.PHONY: install
install: $(STAMP) ## Create .venv and install dependencies

.PHONY: run
run: $(STAMP) ## Run NightBar from source (like npm run dev)
	$(PY) nightbar.py

.PHONY: build
build: $(STAMP) ## Compile a standalone dist/NightBar.app (like npm run build)
	$(PIP) install -q py2app
	rm -rf build dist
	$(PY) setup.py py2app
	@echo "Built dist/NightBar.app"

.PHONY: app
app: build ## Build then launch the .app
	open dist/NightBar.app

.PHONY: clean
clean: ## Remove build output (build/, dist/, __pycache__)
	rm -rf build dist
	find . -type d -name __pycache__ -exec rm -rf {} +

.PHONY: distclean
distclean: clean ## Also remove the virtualenv
	rm -rf $(VENV)

.PHONY: help
help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN{FS=":.*?## "}{printf "  make %-10s %s\n", $$1, $$2}'
