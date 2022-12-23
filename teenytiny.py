import lex
import parse
import emit
import sys


def main():
    print("Teeny Tiny Compiler")

    if len(sys.argv) != 2:
        sys.exit("Error: compiler needs source file as argument.")

    with open(sys.argv[1], "r") as f:
        input = f.read()

    lexer = lex.Lexer(input)
    emitter = emit.Emitter("out.c")
    parser = parse.Parser(lexer, emitter)

    parser.program()
    emitter.write_file()  # Write the output to file.
    print("Compiling completed.")


if __name__ == "__main__":
    main()
