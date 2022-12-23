import lex
from lex import TokenType
import sys

"""
program ::= {statement}
statement ::= "PRINT" (expression | string) nl
    | "IF" comparison "THEN" nl {statement} "ENDIF" nl
    | "WHILE" comparison "REPEAT" nl {statement} "ENDWHILE" nl
    | "LABEL" ident nl
    | "GOTO" ident nl
    | "LET" ident "=" expression nl
    | "INPUT" ident nl
comparison ::= expression (("==" | "!=" | ">" | ">=" | "<" | "<=") expression)+
expression ::= term {( "-" | "+" ) term}
term ::= unary {( "/" | "*" ) unary}
unary ::= ["+" | "-"] primary
primary ::= number | ident
nl ::= '\n'+
"""


class Parser:
    def __init__(self, lexer: lex.Lexer, emitter):
        self.lex = lexer
        self.emitter = emitter
        self.current_token = None
        self.peek_token = None

        self.symbols = set()
        self.labels_declared = set()
        self.labels_gotoed = set()

        self.next_token()
        self.next_token()

    def check_token(self, kind):
        return kind == self.current_token.kind

    def check_peek(self, kind):
        return kind == self.peek_token.kind

    def match(self, kind):
        if not self.check_token(kind):
            self.abort(f"Expected {kind.name}, got {self.current_token.kind.name}")
        self.next_token()

    def next_token(self):
        self.current_token = self.peek_token
        self.peek_token = self.lex.get_token()

    def abort(self, message):
        sys.exit("Error " + message)

    # program ::= {statement}
    def program(self):
        print("PROGRAM")
        # write the header
        self.emitter.header_line("#include <stdio.h>")
        self.emitter.header_line("int main(void){")

        # Clear all newlines before the program begins
        while self.check_token(TokenType.NEWLINE):
            self.next_token()

        # Parse all the statements in the program.
        while not self.check_token(TokenType.EOF):
            self.statement()

        # wrap things up
        self.emitter.emit_line("return 0;")
        self.emitter.emit_line("}")

        for label in self.labels_gotoed:
            if label not in self.labels_declared:
                self.abort("Attempting to GOTO an undeclared label: " + label)

    def statement(self):
        # Check first token to see what kind of statement this is

        if self.check_token(TokenType.PRINT):
            print("STATEMENT-PRINT")
            self.next_token()
            # Simple string
            if self.check_token(TokenType.STRING):
                self.emitter.emit_line(f'printf("{self.current_token.text}\\n");')
                self.next_token()
            else:
                # Expect an expression and print the result as a float.
                self.emitter.emit('printf("%' + '.2f\\n", (float)(')
                self.expression()
                self.emitter.emit_line("));")

        elif self.check_token(TokenType.IF):
            print("STATEMENT-IF")
            self.next_token()
            self.emitter.emit("if(")
            self.comparison()

            self.match(TokenType.THEN)
            self.nl()
            self.emitter.emit_line("){")

            while not self.check_token(TokenType.ENDIF):
                self.statement()

            self.match(TokenType.ENDIF)
            self.emitter.emit_line("}")

        elif self.check_token(TokenType.WHILE):
            print("STATEMENT-WHILE")
            self.next_token()
            self.emitter.emit("while(")
            self.comparison()

            self.match(TokenType.REPEAT)
            self.nl()
            self.emitter.emit_line("){")

            while not self.check_token(TokenType.ENDWHILE):
                self.statement()

            self.match(TokenType.ENDWHILE)
            self.emitter.emit_line("}")

        # "LABEL" ident
        elif self.check_token(TokenType.LABEL):
            print("STATEMENT-LABEL")
            self.next_token()
            if self.current_token.text in self.labels_declared:
                self.abort(f"Label already exists: {self.current_token.text}")
            self.labels_declared.add(self.current_token.text)
            self.emitter.emit_line(self.current_token.text + ":")
            self.match(TokenType.IDENT)

        # "GOTO" ident
        elif self.check_token(TokenType.GOTO):
            print("STATEMENT-GOTO")
            self.next_token()
            self.labels_gotoed.add(self.current_token.text)
            self.emitter.emit_line("goto " + self.current_token.text + ";")
            self.match(TokenType.IDENT)

        # "LET" ident "=" expression
        elif self.check_token(TokenType.LET):
            print("STATEMENT-LET")
            self.next_token()

            #  Check if ident exists in symbol table. If not, declare it.
            if self.current_token.text not in self.symbols:
                self.symbols.add(self.current_token.text)
                self.emitter.header_line("float " + self.current_token.text + ";")

            self.emitter.emit(self.current_token.text + " = ")
            self.match(TokenType.IDENT)
            self.match(TokenType.EQ)

            self.expression()
            self.emitter.emit_line(";")

        # "INPUT" ident
        elif self.check_token(TokenType.INPUT):
            print("STATEMENT-INPUT")
            self.next_token()

            if self.current_token.text not in self.symbols:
                self.symbols.add(self.current_token.text)
                self.emitter.header_line("float " + self.current_token.text + ";")

            # Emit scanf but also validate the input. If invalid, set the variable to 0 and clear the input.
            self.emitter.emit_line(
                f'if(0 == scanf("%f", &{self.current_token.text})) {{'
            )
            self.emitter.emit_line(f"{self.current_token.text} = 0;")
            self.emitter.emit('scanf("%')
            self.emitter.emit_line('*s");')
            self.emitter.emit_line("}")
            self.match(TokenType.IDENT)

        # This is not a valid statement. Error!
        else:
            self.abort(
                "Invalid statement at "
                + self.current_token.text
                + " ("
                + self.current_token.kind.name
                + ")"
            )

        # newline
        self.nl()

    # nl ::= '\n'+
    def nl(self):
        # Require at least one newline.
        self.match(TokenType.NEWLINE)
        # But we will allow extra newlines too, of course.
        while self.check_token(TokenType.NEWLINE):
            self.next_token()

    def is_comparison_op(self):
        return any(
            self.check_token(k)
            for k in [
                TokenType.GT,
                TokenType.LT,
                TokenType.GTEQ,
                TokenType.LTEQ,
                TokenType.EQEQ,
                TokenType.NOTEQ,
            ]
        )

    def comparison(self):
        print("COMPARISON")

        self.expression()

        if self.is_comparison_op():
            self.emitter.emit(self.current_token.text)
            self.next_token()
            self.expression()
        else:
            self.abort(f"Expected comparison operator at {self.current_token.text}")

        # can have 0 or more comparison operator and expressions
        while self.is_comparison_op():
            self.emitter.emit(self.current_token.text)
            self.next_token()
            self.expression()

    def expression(self):
        # expression ::= term {( "-" | "+" ) term}
        print("EXPRESSION")
        self.term()

        while self.check_token(TokenType.PLUS) or self.check_token(TokenType.MINUS):
            self.emitter.emit(self.current_token.text)
            self.next_token()
            self.term()

    def term(self):
        print("TERM")

        self.unary()
        while self.check_token(TokenType.ASTERISK) or self.check_token(TokenType.SLASH):
            self.emitter.emit(self.current_token.text)
            self.next_token()
            self.unary()

    def unary(self):
        print("UNARY")
        if self.check_token(TokenType.PLUS) or self.check_token(TokenType.MINUS):
            self.emitter.emit(self.current_token.text)
            self.next_token()
        self.primary()

    def primary(self):
        print(f"PRIMARY ({self.current_token.text})")

        if self.check_token(TokenType.NUMBER):
            self.emitter.emit(self.current_token.text)
            self.next_token()
        elif self.check_token(TokenType.IDENT):
            if self.current_token.text not in self.symbols:
                self.abort(
                    f"Refrencing variable before assignment: {self.current_token.text}"
                )
            self.emitter.emit(self.current_token.text)
            self.next_token()
        else:
            self.abort(f"Unexpected token at {self.current_token.text}")
