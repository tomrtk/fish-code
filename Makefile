# Makefile

help: ## Show this help message.
	@echo 'usage: make [target] ...'
	@echo
	@echo 'targets:'
	@echo '  clean-all'
	@echo '  clean-venv'

clean-all: clean-venv
	find . -name "__pycache__" -type d -exec $(RM) -r {} +
	find . -name "*.egg-info" -type d -exec $(RM) -r {} +
	find . -name "instance" -type d -exec $(RM) -r {} +
	find . -name ".tox" -type d -exec $(RM) -r {} +
	find . -name ".pytest_cache" -type d -exec $(RM) -r {} +
	find . -name ".coverage" -type f -delete
	$(RM) data.db
	$(RM) -r dist

clean-venv:
	find . -name ".venv" -type d -exec $(RM) -r {} +

.PHONY: help clean-all clean-venv
