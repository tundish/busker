import sys

import busker


def run():
    print(f"Busker {busker.__version__}", file=sys.stdout)
    print("Done.", file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    run()
