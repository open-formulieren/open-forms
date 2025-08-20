# THIS SCRIPT IS ONLY USED IN UNIT TESTS
import django


def main(skip_setup=False):
    if not skip_setup:
        from openforms.setup import setup_env

        setup_env()
        django.setup()

    return False


if __name__ == "__main__":
    main()
