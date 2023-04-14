alias r := run
alias s := shell
alias c := console

shell:
	poetry shell

run:
	poetry run textual run --dev avocet/app.py

console:
	textual console
