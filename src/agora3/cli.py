"""Development entry point; never pretends that an unimplemented runtime is running."""

import argparse

from agora3 import __version__


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="agora3",
        description="Agora3 development skeleton. No world or VM is created.",
        epilog="Start with docs/Start Here.md and docs/Implementation Status.md.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.parse_args()
    parser.print_help()


if __name__ == "__main__":
    main()
