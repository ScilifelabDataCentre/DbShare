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

    def get_expected(self, type, value=None):
        """Return the next token; if it does not match the given type
        or the value (if given), then raise ValueError.
        Tokens of type WHITESPACE are skipped.
        """
        while True:
            try:
                token = next(self)
            except StopIteration:
                raise ValueError
            if token['type'] == 'WHITESPACE': continue
            if token['type'] != type:
                raise ValueError(f"got {token['type']}; expected {type}")
            if value is not None and token['value'] != value:
                raise ValueError(f"got {token['value']}; expected {value}")
            return token

    def split_reserved(self, words):
        """Split all tokens at reserved words in the order given.
        Return map of reserved words to lists of subsequent tokens.
        """
        words = set(words)
        tokens = list(self)
        for token in tokens:
            if token['type'] == 'RESERVED' and token['value'] in words:
                token['split'] = True
            else:
                token['split'] = False
        result = {}
        word = None
        for token in tokens:
            if token['split']:
                word = token['value']
            elif word:
                result.setdefault(word, []).append(token)
        return result

    def get_until(self, type, value=None):
        """Return the list of tokens until one is reached that matches
        the given type and value (if given, possibly as tuple).
        Tokens of type WHITESPACE are skipped.
        The token that stopped the search is available in 'self.until_token'.
        """
        result = []
        self.until_token = None
        print('until', value)
        try:
            while True:
                token = next(self)
                print(token)
                if token['type'] == 'WHITESPACE': continue
                if token['type'] == type:
                    if value is None: break
                    if token['value'] == value: break
                    if isinstance(value, (tuple, list)) and \
                       token['value'] in value: break
                result.append(token)
        except StopIteration:
            self.until_token = None
            print('Stop', result)
            return result
        else:
            self.until_token = token
            print(result)
            return result


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
    lexer(sql)
    for token in lexer:
        print(token)
    print()
    sql = 'SELECT DISTINCT x, "abn.z" AS a FROM w, abn WHERE w.id>abn."x-e-w" LIMIT 100'
    lexer(sql)
    lexer.get_expected('RESERVED')
    lexer.get_expected('RESERVED')
    print(lexer.get_expected('IDENTIFIER'))
    try:
        lexer.get_expected('IDENTIFIER')
    except ValueError:
        pass
    else:
        raise ValueError('should not reach this')
    words = lexer.split_reserved(['FROM', 'WHERE', 'LIMIT', 'OFFSET'])
    for word, tokens in words.items():
        print(word, tokens)
