PYTHON ?= python3
STUDIO := $(PYTHON) tools/studio.py
CONTINUITY := $(PYTHON) tools/continuity.py

.PHONY: start status resume checkpoint audit list doctor validate test manifest hydrate-wf01 hydrate-wf03 videogen-check videogen-plan clean

start:
	$(CONTINUITY) resume

status:
	$(CONTINUITY) status

resume:
	$(CONTINUITY) resume

checkpoint:
	@echo 'Use: python3 tools/continuity.py checkpoint --summary "..." --next-action "..." --commit --push'

audit:
	$(CONTINUITY) audit --max-age-minutes 70

list:
	$(STUDIO) list

doctor:
	$(STUDIO) doctor

validate:
	$(STUDIO) validate

test:
	$(PYTHON) -m unittest discover -s tests -v

manifest:
	$(STUDIO) manifest --write

videogen-check:
	$(PYTHON) tools/videogen.py doctor

videogen-plan:
	@echo 'Use: python3 tools/videogen.py plan workflows/current/payload/<project>/project.json'

hydrate-wf01:
	$(STUDIO) hydrate wf01 --force

hydrate-wf03:
	$(STUDIO) hydrate wf03 --force

clean:
	$(STUDIO) clean all

.PHONY: materialize-status materialize-compact materialize-full
materialize-status:
	$(PYTHON) tools/materialize.py status

materialize-compact:
	$(PYTHON) tools/materialize.py compact

materialize-full:
	$(PYTHON) tools/materialize.py full
