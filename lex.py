import enum
import sys
from dataclasses import dataclass


class TokenType(enum.Enum):
    EOF = -1
    NEWLINE = 0
    NUMBER = 1
    IDENT = 2
    STRING = 3
    # Keywords.
    LABEL = 101
    GOTO = 102
    PRINT = 103
    INPUT = 104
    LET = 105
    IF = 106
    THEN = 107
    ENDIF = 108
    WHILE = 109
    REPEAT = 110
    ENDWHILE = 111
    # Operators.
    EQ = 201
    PLUS = 202
    MINUS = 203
    ASTERISK = 204
    SLASH = 205
    EQEQ = 206
    NOTEQ = 207
    LT = 208
    LTEQ = 209
    GT = 210
    GTEQ = 211


@dataclass
class Token:
    text: str
    kind: TokenType

    @staticmethod
    def is_keyword(text):
        for kind in TokenType:
            if kind.name == text and 100 <= kind.value <= 200:
                return kind
        return None


class Lexer:
    def __init__(self, input: str):
        self.source = input + "\n"
        self.source_len = len(self.source)
        self.char = ""
        self.pos = -1
        self.next_char()

    def next_char(self):
        self.pos += 1
        if self.pos >= self.source_len:
            self.char = "\0"
        else:
            self.char = self.source[self.pos]

    def peek(self) -> str:
        if self.pos + 1 >= self.source_len:
            return "\0"
        return self.source[self.pos + 1]

    def abort(self, message):
        sys.exit("Lexing error. " + message)

    def skip_whitespace(self):
        while self.char in [" ", "\t", "\r"]:
            self.next_char()

    def skip_comment(self):
        if self.char == "#":
            while self.char != "\n":
                self.next_char()

    def get_token(self):
        self.skip_whitespace()
        self.skip_comment()
        token = None
        if self.char == "+":
            token = Token(self.char, TokenType.PLUS)
        elif self.char == "-":
            token = Token(self.char, TokenType.MINUS)
        elif self.char == "*":
            token = Token(self.char, TokenType.ASTERISK)
        elif self.char == "/":
            token = Token(self.char, TokenType.SLASH)
        elif self.char == "=":
            if self.peek() == "=":
                last_char = self.char
                self.next_char()
                token = Token(last_char, TokenType.EQEQ)
            else:
                token = Token(self.char, TokenType.EQ)
        elif self.char == ">":
            # Check whether this is token is > or >=
            if self.peek() == "=":
                last_char = self.char
                self.next_char()
                token = Token(last_char + self.char, TokenType.GTEQ)
            else:
                token = Token(self.char, TokenType.GT)
        elif self.char == "<":
            # Check whether this is token is < or <=
            if self.peek() == "=":
                last_char = self.char
                self.next_char()
                token = Token(last_char + self.char, TokenType.LTEQ)
            else:
                token = Token(self.char, TokenType.LT)
        elif self.char == "!":
            if self.peek() == "=":
                last_char = self.char
                self.next_char()
                token = Token(last_char + self.char, TokenType.NOTEQ)
            else:
                self.abort("Expected !=, got !" + self.peek())
        elif self.char == '"':
            self.next_char()
            start = self.pos

            while self.char != '"':
                if self.char in ("\r", "\t", "\n", "//", "%"):
                    self.abort("Illegal character in string.")
                self.next_char()
            text = self.source[start : self.pos]
            token = Token(text, TokenType.STRING)
        elif self.char.isdigit():
            start = self.pos
            while self.peek().isdigit():
                self.next_char()
            if self.peek() == ".":
                self.next_char()
                if not self.peek().isdigit():
                    self.abort(f"illegal character in number at {self.pos}")
                while self.peek().isdigit():
                    self.next_char()
            text = self.source[start : self.pos + 1]
            token = Token(text, TokenType.NUMBER)
        elif self.char.isalpha():
            start = self.pos
            while self.peek().isalnum():
                self.next_char()

            text = self.source[start : self.pos + 1]
            keyword = Token.is_keyword(text)
            if keyword is None:
                token = Token(text, TokenType.IDENT)
            else:
                token = Token(text, keyword)
        elif self.char == "\n":
            token = Token(self.char, TokenType.NEWLINE)
        elif self.char == "\0":
            token = Token(self.char, TokenType.EOF)
        else:
            self.abort("Unknown token: " + self.char)

        self.next_char()
        return token


def main():
    input = '+- */ != == > # this is a comment\n <= >= > "foobar" 32313 3.13 foobar LET PRINT'
    lexer = Lexer(input)
    token = lexer.get_token()
    while token.kind != TokenType.EOF:
        print(token.kind)
        token = lexer.get_token()


if __name__ == "__main__":
    main()
