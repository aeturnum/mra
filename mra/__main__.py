import sys
import os

from mra.settings import Settings
from mra.dynamic_module import DynamicModuleManager
from mra.management import MRAManager

# credit
# https://chriswarrick.com/blog/2014/09/15/python-apps-the-right-way-entry_points-and-scripts/

def main(args=None):
    """The main routine."""
    if args is None:
        args = sys.argv[1:]

    mm = MRAManager(args)
    mm.run()


if __name__ == "__main__":
    main()