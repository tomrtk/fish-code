# Makefile

help: ## Show this help message.
	@echo 'usage: make [target] ...'
	@echo
	@echo 'targets:'
	@echo '  clean-poetry-lock'
	@echo '  clean-venv'

clean-poetry-lock:
	find . -name "poetry.lock" -type f -delete

clean-venv:
	find . -name ".venv" -type d -exec $(RM) -r {} +

.PHONY: help clean-poetry-lock clean-venv
