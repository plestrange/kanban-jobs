.PHONY: init dev test check-clean

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
	./scripts/check-clean.sh

check-clean:
	./scripts/check-clean.sh
