"Extract tokens from text according to given regexp-based rules."

import re

class Lexer:
    "Extract tokens from text according to given regexp-based rules."

    def __init__(self, rules, text=''):
        self.rules = []
        for rule in rules:
            self.add_rule(rule['name'],
                          rule['regexp'],
                          convert=rule.get('convert'),
                          case=rule.get('case', False))
        self.set(text)

    def __call__(self, text):
        self.set(text)
        return self

    def __iter__(self):
        return self

    def __next__(self):
        try:
            line = self.lines[self.nline]
        except IndexError:
            raise StopIteration
        if self.pos >= len(line):
            self.nline += 1
            self.pos = 0
        for rule in self.rules:
            match = rule['rx'].match(line, self.pos)
            if match is not None:
                break
        else:
            raise ValueError(self.message())
        raw = line[match.start() : match.end()]
        token = {'name': rule['name'], 'raw': raw}
        token.update(match.groupdict())
        convert = rule['convert']
        if convert is None:
            token['value'] = token['raw']
        else:
            try:
                convert(token)
            except Exception as error:
                raise ValueError(f"invalid token at {self.location()}; {error}")
        self.pos += len(raw)
        return token

    def set(self, text):
        self.lines = text.split('\n')
        self.nline = 0
        self.pos = 0

    def add_rule(self, name, regexp, convert=None, case=False):
        if case:
            rx = re.compile(regexp)
        else:
            rx = re.compile(regexp, re.IGNORECASE)
        if isinstance(convert, str):
            convert = getattr(self, convert)
        self.rules.append({'name': name,
                           'regexp': regexp,
                           'rx': rx,
                           'convert': convert})

    def location(self):
        "Return info on current location in text."
        return f"line {self.nline}, position {self.pos}"

    def integer(self, token):
        "Convert the raw value to an integer (=int)."
        token['value'] = int(token['raw'])

    def real(self, token):
        "Convert the raw value to a real (=float)."
        token['value'] = float(token['raw'])

    def upcase(self, token):
        "Convert the raw value to upper case characters."
        token['value'] = token['raw'].upper()

    def quotechar_strip(self, token):
        "Remove the quotechar from the start and end of the raw value."
        token['value'] = token['raw'].strip(token['quotechar'])
