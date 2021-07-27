# Makefile

venv := .venv
activate := $(venv)/bin/activate
src_files := $(shell find src -type f -iname '*.py')

.PHONY: help clean-all clean-venv deps nina run venv

help: ## Show this help message.
	@echo 'usage: make [venv=<name>] [target] ...'
	@echo
	@echo 'targets:'
	@echo '  clean-all      Delete all build/dev associated files'
	@echo '  clean-venv     Delete the virtual environment'
	@echo '  deps-cpu       Install dependencies in a virtual environment'
	@echo '  deps-gpu       Install dependencies in a virtual environment'
	@echo '  nina           Build nina in a virtual environment'
	@echo '  run            Run nina in a virtual environment'
	@echo '  venv           Create a virtual environment'
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
	find . -name "venv" -type d -exec $(RM) -r {} +
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

.make.deps.cpu: .make.deps
	@. $(activate) && \
	pip install -e '.[cpu]' && \
	touch $@

.make.deps.gpu: .make.deps
	@. $(activate) && \
	pip install -e '.[gpu]' --find-links https://download.pytorch.org/whl/torch_stable.html && \
	touch $@

deps-cpu: .make.deps.cpu

deps-gpu: .make.deps.gpu
