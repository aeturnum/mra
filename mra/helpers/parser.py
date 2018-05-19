from mra.dynamic_module import DynamicModuleManager
from mra.settings import SettingsError
from mra.helpers.logger import Logger

# why do I always do this to myself?
# TODO: Add support for kwargs
class ArgParser(Logger):
    _seps = ('(', ',')

    def __init__(self, arg_str: str):
        super().__init__()
        self.args = arg_str
        self.dmm = DynamicModuleManager()
        self._adopt(self.dmm)

    def _edge_trim(self, s: str, ends:str):
        if s[0] == ends[0] and s[-1] == ends[-1]:
            s = s[1:-1]

        return s

    @staticmethod
    def _convert(arg, converter):
        if type(arg) is str:
            try:
                arg = converter(arg)
            except ValueError:
                pass
        return arg

    def _process_call(self, arg: str):
        self.log_spew(f"Processing call: {arg}")
        arg = arg.strip()
        loc = arg.find('(')
        name, inner_args = arg[:loc], arg[loc:]
        self.log_spew(f"Call split: {name}({inner_args})")
        try:
            cls = self.dmm.LoadClass(name)
        except SettingsError:
            self.log_warn(f"Tried to load {arg} as a call, but did not find object! Treating as string.")
            # treat it as a string literal
            return self._process_arg(arg)

        self.log_spew(f"Creating action parser to handle {inner_args}")
        sub_ap = ArgParser(inner_args)
        self._adopt(sub_ap)
        sub_ap = [a for a in sub_ap]
        self.log_spew(f"Creating {cls} with args {sub_ap}")
        action = cls(*sub_ap)

        return action


    def _process_arg(self, arg: str):
        self.log_spew(f"Processing argument: {arg}")
        arg = arg.strip()
        arg = self._convert(arg, int)
        arg = self._convert(arg, float)
        # normalize strings
        if type(arg) is str:
            # strip quotes and escapes
            arg = arg.strip('\'"\\')

        self.log_spew(f"Processed: {arg}")
        return arg

    def _next_sep(self, s: str):
        min = [None]
        distance = [(sep, s.find(sep)) for sep in self._seps]
        for d in distance:
            # not found
            if d[1] == -1:
                continue

            if min[0] is None:
                min = d
            if d[1] < min[1]:
                min = d

        return min[0]

    def _match_parens(self, s: str):
        parens = []
        for idx, c in enumerate(s):
            if c == '(':
                parens.append('(')
            if c == ')':
                if len(parens) == 0:
                    raise Exception(f"Something has gone wrong parsing {s}")
                parens.pop()
                if len(parens) == 0:
                    return idx + 1

        raise Exception(f"Unmatched parens in {s}")

    def __iter__(self):
        self.log_system("Begining parse of {}", self.args)
        args = self.args.strip()  # whitespace
        args = self._edge_trim(args, '()')
        self.log_spew("Post-trimming arg: {}", args)

        # are you ready for amateur parsing code?
        while True:
            self.log_spew(f"Begin loop: '{args}'")
            # we don't care about white space
            args = args.strip()
            self.log_spew(f"post-strip: '{args}'")

            if args == '':
                # done
                self.log_spew(f"Args parsed!")
                break

            # can be left after parsing an object
            if args[0] == ',':
                args = args[1:]
                self.log_spew(f"removed comma: '{args}'")

            sep = self._next_sep(args)
            self.log_spew(f"found next seperator: {sep} - '{args}'")
            if sep == '(':
                # open paren before a comma. We need to count open / close parens
                idx = self._match_parens(args)
                self.log_spew(f"found next paren: {idx} - '{args}'")
                arg, args = args[:idx], args[idx:]
                self.log_spew(f"split args: '{arg}':'{args}'")
                yield self._process_call(arg)
            elif sep == ',':
                # comma before paren. Easy case
                arg, args = args.split(',', 1)
                self.log_spew(f"split on comma: '{arg}':'{args}'")
                yield self._process_arg(arg)
            elif sep == None:
                self.log_spew(f"final arg!: '{args}'")
                yield self._process_arg(args)
                break
            else:
                raise Exception(f"huh?: {args}")