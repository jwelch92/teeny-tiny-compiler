class Emitter:
    def __init__(self, outfile):
        self.outfile = outfile
        self.header = ""
        self.code = ""

    def emit(self, code):
        self.code += code

    def emit_line(self, code):
        self.code += code + "\n"

    def header_line(self, code):
        self.header += code + "\n"

    def write_file(self):
        with open(self.outfile, "w") as f:
            f.write(self.header + self.code)
