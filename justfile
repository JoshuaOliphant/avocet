set positional-arguments

alias r := run
alias s := shell
alias c := console
alias i := install
alias t := test
alias p := push

shell:
	poetry shell

install:
	poetry install

run:
	poetry run textual run --dev avocet/app.py

console:
	textual console

test:
    poetry run pytest

push:
    git push origin main

commit message:
    git commit -am {{message}}
