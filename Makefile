VERSION := $(shell python3 -c 'import json; print(json.load(open("plugins/writing/.claude-plugin/plugin.json"))["version"])')

.PHONY: pack release lint

pack:
	scripts/pack.sh

release:
	@test -z "$$(git status --porcelain --untracked-files=no)" || { echo "working tree has uncommitted changes"; exit 1; }
	@git rev-parse "v$(VERSION)" >/dev/null 2>&1 && { echo "tag v$(VERSION) exists"; exit 1; } || true
	scripts/pack.sh
	git tag -a "v$(VERSION)" -m "writing $(VERSION)"
	@echo "tagged v$(VERSION). Push it with: git push origin v$(VERSION)"

lint:
	python3 plugins/writing/scripts/writing_lint.py $$(git ls-files '*.md')
