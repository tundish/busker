import argparse
import sys

from balladeer import discover_assets

import busker


def main(args):
    assets = discover_assets(args.source, "")
    print(f"Busker {busker.__version__}", file=sys.stderr)
    print(f"{assets}", file=sys.stdout)
    print("Done.", file=sys.stderr)
    return 0

def parser():
    rv = argparse.ArgumentParser()
    rv.add_argument("source", help="Set path to source directory.")
    return rv

def run():
    p = parser()
    args = p.parse_args()
    rv = main(args)
    sys.exit(rv)


if __name__ == "__main__":
    run()
