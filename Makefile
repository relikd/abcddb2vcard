.PHONY: install
install:
	[ -z "$${VIRTUAL_ENV}" ] \
	&& python3 -m pip install -e . --user \
	|| python3 -m pip install -e .

.PHONY: uninstall
uninstall:
	python3 -m pip uninstall abcddb2vcard
	rm -rf ./*.egg-info/
	@-rm -i "$$(which abcddb2vcard)" "$$(which vcard2img)"

dist: setup.py abcddb2vcard/*
	[ -z "$${VIRTUAL_ENV}" ]  # you can not do this inside a virtual environment.
	@echo Building...
	python3 setup.py sdist bdist_wheel
	rm -rf ./*.egg-info/ ./build/ MANIFEST

env-publish:
	@echo Creating virtual environment...
	@python3 -m venv 'env-publish'
	@source env-publish/bin/activate && pip install twine

.PHONY: publish
publish: dist env-publish
	[ -z "$${VIRTUAL_ENV}" ]  # you can not do this inside a virtual environment.
	@echo Publishing...
	@echo "\033[0;31mEnter PyPI token in password prompt:\033[0m"
	@source env-publish/bin/activate && export TWINE_USERNAME='__token__' && twine upload dist/*
