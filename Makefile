# This Makefile is based on the Makefile defined in the Python Best Practices repository:
# https://git.data.amsterdam.nl/Datapunt/python-best-practices/blob/master/dependency_management/

PYTHON = python3

pip-tools:
	pip install pip-tools

requirements: pip-tools             ## Upgrade requirements (in requirements-root.txt) to latest versions and compile requirements.txt
	pip-compile --upgrade --output-file requirements.txt requirements-root.txt

diff:
	@python3 ./scripts/diff.py
