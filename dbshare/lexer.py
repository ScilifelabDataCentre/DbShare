"Extract tokens from text according to given regexp-based rules."

import re

class Lexer:
    "Extract tokens from text according to given regexp-based rules."

    def __init__(self, rules, text=''):
        self.rules = []
        for rule in rules:
            self.add_rule(rule['type'],
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
            try:
                line = self.lines[self.nline]
            except IndexError:
                raise StopIteration
        for rule in self.rules:
            match = rule['rx'].match(line, self.pos)
            if match: break
        else:
            raise ValueError(self.location())
        self.pos += match.end() - match.start()
        token = {'type': rule['type'], 
                 'raw': line[match.start() : match.end()]}
        token.update(match.groupdict())
        convert = rule['convert']
        if convert is None:
            token['value'] = token['raw']
        else:
            try:
                convert(token)
            except Exception as error:
                raise ValueError(f"invalid token at {self.location()}; {error}")
        return token

    def set(self, text):
        self.lines = text.split('\n')
        self.nline = 0
        self.pos = 0

    def add_rule(self, type, regexp, convert=None, case=False):
        if case:
            rx = re.compile(regexp)
        else:
            rx = re.compile(regexp, re.IGNORECASE)
        if isinstance(convert, str):
            convert = getattr(self, convert)
        self.rules.append({'type': type,
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


if __name__ == '__main__':
    lexer = Lexer([
        {'type': 'RESERVED',
         'regexp': r"SELECT|DISTINCT|FROM|AS|WHERE|ORDER|BY|AND|OR|NOT|LIMIT",
         'case': False,
         'convert': 'upcase'},
        {'type': 'INTEGER', 'regexp': r"-?\d+", 'convert': 'integer'},
        {'type': 'DELIMITER', 'regexp': r"!=|>=|<=|[-+/*<>=\?\.,;\(\)]"},
        {'type': 'WHITESPACE', 'regexp': r"\s+"},
        {'type': 'IDENTIFIER', 'regexp': r"[a-z]\w*", 'case': False},
        {'type': 'IDENTIFIER',
         'regexp': r"(?P<quotechar>[\'|\"])\S+(?P=quotechar)",
         'case': False,
         'convert': 'quotechar_strip'}
    ])
    sql = 'SELECT DISTINCT x, "abn.z" AS a FROM w, abn WHERE w.id>abn."x-e-w"'
    for token in lexer(sql):
        print(token)
