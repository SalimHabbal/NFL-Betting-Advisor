"""Module entrypoint for python -m execution."""

# Delegates to the CLI main function when invoked as a module
from .cli import main

if __name__ == "__main__":
    main()
