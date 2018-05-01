from mra.actions.action import ArgStandin


class ArgFromList(ArgStandin):
    PATH = 'ArgFromList'
    def __init__(self, lst:list):
        super().__init__()
        self.list = lst

    def __iter__(self):
        for v in self.list:
            yield v

    def __str__(self):
        return f'ArgFromList({len(self.list)}items)'

class ArgFromFile(ArgStandin):
    PATH = 'ArgFromFile'
    def __init__(self, filename):
        super().__init__()
        self.filename = filename

    def __iter__(self):
        with open(self.filename, 'r') as f:
            for line in f:
                # eliminate whitespace
                line = line.strip()
                # allow comments
                if line[0] in ['#']:
                    # don't load
                    continue
                yield line

    def __str__(self):
        return f'ArgFromFile({self.filename})'