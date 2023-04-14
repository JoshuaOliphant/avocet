alias r := run
alias s := shell
alias c := console
alias i := install

shell:
	poetry shell

install:
	poetry install

run:
	poetry run textual run --dev avocet/app.py

console:
	textual console
