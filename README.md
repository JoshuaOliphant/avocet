[![Python application](https://github.com/JoshuaOliphant/avocet/actions/workflows/python-app.yml/badge.svg)](https://github.com/JoshuaOliphant/avocet/actions/workflows/python-app.yml)

# Avocet

Avocet is a TUI the accesses the [Raindrop API](https://developer.raindrop.io/). It is written in Python and uses the [Textual Framework](https://textual.textualize.io). It also summarizes each bookmark as it is loaded and displays the summary, and opens the bookmark link in the default browser.

## Requirements

- Python 3
- [Poetry](https://python-poetry.org/docs/)
- [Just](https://github.com/casey/just)

## Getting Started

1. Clone the repo
1. Run `just install` or `poetry install` to install dependencies
1. Set your Raindrop.io API token as the environment variable `RAINDROP`.
1. Run `just run` or `poetry run avocet` to run the
1. Tab between sections. Use the arrow keys to navigate within a section. Press enter in the collections section to view the bookmarks in that collection. Press enter on a bookmark to open it in your default browser. Press `ctrl-c` to quit.
1. View the [justfile](./justfile) for more commands.
1. Note: it can take a while to load the first time it is started, because it has to contact OpenAI to summarize each bookmark. Speeding this process up is on my Todo list.

![Screenshot](./media/Screenshot.png)
