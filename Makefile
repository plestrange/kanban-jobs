.PHONY: init dev test check-clean check-staged lint typecheck docs

DATA_PATTERN := ^(data/|config/criteria\.yaml$$)

init:
	mkdir -p data/inbox data/cards
	test -f data/criteria.yaml || cp config/criteria.example.yaml data/criteria.yaml
	cp hooks/pre-commit .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit
	@echo "data/ ready; pre-commit hook installed. Edit data/criteria.yaml and write data/profile.md next."

dev:
	FLASK_APP=app.server FLASK_DEBUG=1 flask run

test:
	pytest
	$(MAKE) check-clean

# Tracked paths that must stay gitignored — see docs/ARCHITECTURE.md §9.
check-clean:
	@bad=$$(git ls-files | grep -E '$(DATA_PATTERN)' || true); \
	if [ -n "$$bad" ]; then \
		echo "ERROR: tracked paths that must stay gitignored:" >&2; \
		echo "$$bad" >&2; \
		exit 1; \
	fi; \
	echo "check-clean: no data/ paths tracked."

# Same check, scoped to what's about to be committed — run by hooks/pre-commit.
check-staged:
	@bad=$$(git diff --cached --name-only | grep -E '$(DATA_PATTERN)' || true); \
	if [ -n "$$bad" ]; then \
		echo "Refusing commit — staged path(s) under data/ or config/criteria.yaml:" >&2; \
		echo "$$bad" >&2; \
		echo "This data must never enter git history. See docs/ARCHITECTURE.md §9." >&2; \
		exit 1; \
	fi

lint:
	ruff check .

typecheck:
	mypy src app

docs:
	sphinx-build -b html docs docs/_build/html
