set positional-arguments

alias r := run
alias t := test
alias i := install
alias l := lint

install:
	uv sync

run:
	uv run textual run --dev avocet/app.py

console:
	uv run textual console

test:
	uv run pytest

snapshot-update:
	uv run pytest --snapshot-update

lint:
	uv run ruff check .

format:
	uv run ruff format .

typecheck:
	uv run ty check

commit message:
	git commit -am "$1"
