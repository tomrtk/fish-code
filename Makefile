# Makefile

venv := .venv
activate := $(venv)/bin/activate
src_files := $(shell find src -type f -iname '*.py')

.PHONY: help clean-all clean-venv deps nina run venv

help: ## Show this help message.
	@echo 'usage: make [venv=<name>] [target] ...'
	@echo
	@echo 'targets:'
	@echo '  clean-all      Deletes all build/dev associated files'
	@echo '  clean-venv     Deletes the virtual environment'
	@echo '  deps           Installs dependencies in a virtual environment'
	@echo '  nina           Builds nina in a virtual environment'
	@echo '  run            Runs nina in a virtual environment'
	@echo '  venv           Creates a virtual environment'
	@echo
	@echo 'Variables:'
	@echo '  venv           Set your own venv name. Do not use `venv` as it may'
	@echo '                 cause circular dependencies.'

clean-all: clean-venv
	find . -name "__pycache__" -type d -exec $(RM) -r {} +
	find . -name "*.egg-info" -type d -exec $(RM) -r {} +
	find . -name "instance" -type d -exec $(RM) -r {} +
	find . -name ".tox" -type d -exec $(RM) -r {} +
	find . -name ".pytest_cache" -type d -exec $(RM) -r {} +
	find . -name ".coverage" -type f -exec $(RM) -r {} +
	$(RM) data.db
	$(RM) -r dist

clean-venv:
	find . -name "$(venv)" -type d -exec $(RM) -r {} +
	find . -name ".make.deps" -type f -exec $(RM) -f {} +

venv: $(venv)

$(venv):
	virtualenv $(venv) --download

$(venv)/bin/nina: $(src_files) $(venv)
	@. $(activate) && \
	pip install -e .

nina: $(venv)/bin/nina

run: nina
	@. $(activate) && \
	python -m nina

.make.deps: setup.cfg $(venv) $(venv)/bin/nina
	@. $(activate) && \
	pip install -e '.[dev,testing]' && \
	touch $@

deps: .make.deps
