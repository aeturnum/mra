import json
import json5
import collections

from operator import itemgetter, setitem


class UpdatableDict(dict):
    @classmethod
    def create_from_dict(cls, d:dict):
        result = cls()
        result.update_and_check(d)
        return result

    # helper to create a property
    @staticmethod
    def _variable_property(key, default=None):

        def getter(self):
            return self.get(key, default)

        def setter(self, v):
            setitem(self, key, v)

        def deleter(self):
            if key in self:
                del self[key]

        return property(getter, setter, deleter)

    def update_and_check(self, info: dict):
        for key, value in info.items():
            if key not in self or self.get(key) == None:
                if hasattr(self, key):
                    setattr(self, key, value)
                else:
                    setitem(self, key, value)
            else:
                if not verbose_equals(self[key], value):
                    raise Exception(
                        f'While updating a Terminal, non-matching info was found for "{key}": {value} != {self[key]}'
                    )

def verbose_equals(a:dict, b:dict):
    # check types are same, otherwise false
    if type(a) is not type(b):
        return False
    # if we're in a dict, check all keys
    if type(a) is dict:
        for k, v in a.items():
            if not verbose_equals(v, b[k]):
                return False
    # if we're in a list, check all members
    # order matters!
    elif type(a) is list:
        for idx, v in enumerate(a):
            if not verbose_equals(v, b[idx]):
                return False
    # else just check values
    else:
        return a == b
    # todo: sets and other data types I'm not using at the moment

    return True

def mod_path(*args):
    return '.'.join(args)

def load_json(json_string:str):
    j = None
    try:
        j = json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        # don't catch this log_error if it happens
        j = json5.loads(json_string)

    return j

class ClassInfo(object):
    def __init__(self, cls:type):
        # print(f'ClassInfo({cls})')
        self.name = cls.__name__
        self.module = cls.__module__
        self._class = cls

    def full_name(self):
        return f'{self.module}.{self.name}'

    def supers(self):
        return self._class.__bases__

    @property
    def rev_module_list(self):
        # we reverse this because different package contexts can cause different path lengths
        # ex:
        # <class 'task_generator.MultipleActions'>
        # <class 'mra.task_generator.MultipleActions'>
        # these are the same class, but one is imported from a frame where we're aware of the
        # mra package. So we compare in reverse order and, if they match, allow the final and unbalanced
        # reference to be there
        mod_list = self.module.split('.')
        mod_list.reverse()
        return mod_list

    def __eq__(self, other:'ClassInfo'):
        if type(other) is not ClassInfo:
            # print(f'{self} != {other}: other is not ClassInfo')
            return False

        if other.name != self.name:
            # print(f'{self} != {other}: other has wrong name')
            return False

        other_mods = other.rev_module_list
        at_least_one_matched = False
        for idx, mod in enumerate(self.rev_module_list):
            # see note in rev_module_list for why we do it this way
            if idx + 1 > len(other_mods):
                # print(f'idx {idx} not in other mods!')
                # print(f'{idx + 1} <= {len(other_mods)}')
                break
            # always set this to the last comparison we can make
            at_least_one_matched = (mod == other_mods[idx])
            # print(f'{at_least_one_matched} = ({mod} == {other_mods[idx]})')
            # if it's ever false, we can stop and return false
            if not at_least_one_matched:
                break

        # print(f'{self} ?= {other}: {at_least_one_matched}')
        return at_least_one_matched

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return self.full_name()

    def __repr__(self):
        return self.full_name()

def is_instance(object:object, container_or_class):
    """
    This function exists because Python is not perfect at managing class meta-objects
    reference: https://stackoverflow.com/questions/49838163/class-identification-in-dynamically-loaded-classes-v-s-classes-loaded-by-import/49838272#49838272
    Normally, the builtin isinstance() would be fine, but because we create classes by loading directly from files
    dynamically, the metaclass objects end up being duplicated and Python can't be sure they're of the same class
    hierarchy (technically, as the SO answer says, they are not - they simply have identical source code).

    So I created this method to determine, as best we can, if two classes share lineage. It's not perfect, but
    it should be sufficient.

    :param Object object:
    :param class object or list of class objects container_or_class:
    :return: True if object is a subclass of any of the classes in container_or_class
    """
    if hasattr(object, '__class__'):
        # extract class object
        # todo: check if the object is already a class, even though it shouldn't be
        object = object.__class__

    # put it in a list
    # if not hasattr(container_or_class, '__getitem__'):
    if not isinstance(container_or_class, collections.Iterable):
        container_or_class = [container_or_class]
    matching_classes = [ClassInfo(cls) for cls in container_or_class]

    # prevent dupes
    super_class_set = set()
    super_classes = []
    # base class
    class_objects = [ClassInfo(object)]
    # gather superclasses
    class_objects.extend([ClassInfo(cls) for cls in object.__bases__])

    while True:
        new_class_objects = []
        for ci in class_objects:
            # short circut
            if ci in matching_classes:
                # print(f'class {ci} is in {matching_classes}')
                return True

            super_classes.append(ci)
            super_class_set.add(ci.full_name())
            for scls in ci.supers():
                scls_ci = ClassInfo(scls)
                if scls_ci.full_name() not in super_class_set:
                    new_class_objects.append(scls_ci)
        # these objects are processed now
        class_objects.clear()
        class_objects = new_class_objects

        # stop when we're done with new objects
        if not class_objects:
            break

    # print(f'{object} did not match any of {matching_classes}')
    return False
