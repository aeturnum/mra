import sys
import os

from mra.settings import Settings
from mra.dynamic_module import DynamicModuleManager
from mra.management import JobSpec

# credit
# https://chriswarrick.com/blog/2014/09/15/python-apps-the-right-way-entry_points-and-scripts/

def main(args=None):
    """The main routine."""
    if args is None:
        args = sys.argv[1:]

    s = Settings.load_from_file()
    DynamicModuleManager.gather(s)
    for job in JobSpec.load_directory(s, os.getcwd()):
        print('creating plan')
        plan = job.create_plan()
        print('running plan')
        plan.run()


if __name__ == "__main__":
    main()