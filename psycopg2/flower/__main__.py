from flower.command import FlowerCommand
from flower.utils import bugreport


def main():
    try:
        flower = FlowerCommand()
        flower.execute_from_commandline()
    except Exception:
        import sys
        print(bugreport(app=flower.app), file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
