SRCS=\
     $(wildcard core/*.py) \
     $(wildcard repository/*.py)

all: test

test:
	pytest

coverage:
	coverage run -m pytest && coverage report -m

coverage-html:
	coverage run -m pytest && coverage html

check-docs:
	pydocstyle $(SRC) --convention=numpy

clean:
	-@$(RM) -r $(wildcard *.pyc __pycache__ htmlcov .coverage)

.PHONY: all test clean coverage check-docs
