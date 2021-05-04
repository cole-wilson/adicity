import sys


class AdicityError(Exception):
	errorcode = -99

	@staticmethod
	def highlight(program_code, row, col, endcol=None, linestoshow=10):
		row = row + 1
		out = []
		program_code = program_code.split('\n')
		linestoshow = min(row-1, linestoshow)
		linenum_len = len(str(row))
		for i in range(row-linestoshow, row):
			out.append(
				f"{str(i).rjust(linenum_len)}: {program_code[i - 1]}"
			)
		endmarker = "^"
		if col < 0 or col > len(program_code[i - 1]):
			col = len(program_code[i - 1]) + 1
		if endcol is None or endcol > len(program_code[i - 1]):
			endcol = col
			endmarker = ""
		out.append(f"{'^'.rjust(linenum_len+2+col)}{endmarker.rjust(endcol-col,'-')}")
		return "\n".join(out)

	def descriptor(self, description, program, token, col=None):
		if col is None:
			col = token.linepos
		return f"{self.highlight(program, token.line, col)}\n" \
				f"{type(self).__name__}: {description} at token {token} " \
				f"(row {token.line}, col {token.linepos})"

	def pretty(self, program):
		return self.descriptor(self.desc, program, self.token)

	def __init__(self, token):
		self.token = token
		super().__init__()


class AdicityRecursionError(AdicityError):
	desc = "Recursion limit exceeded at"
	errorcode = 5


class AdicityTypeError(AdicityError):
	desc = "Array returned floating point integer"
	errorcode = 6


class AdicityEOFError(AdicityError):
	desc = f"Unexpected end of file while parsing token"
	errorcode = 9

	def pretty(self, program):
		return self.descriptor(self.desc, program, self.token, col=-1)


class AdicityTokenError(AdicityError):
	@property
	def desc(self):
		return f"Found unknown token while lexing. Namespace `{self.namespace}`, "
	errorcode = 2

	def __init__(self, token, namespace):
		self.token = token
		self.namespace = namespace


class InvalidAdicityCharacter(AdicityError):
	errorcode = 3

	@property
	def pretty(self):
		return f"Unable to coerce integer to character while echoing.\n" \
			f"Maximum systemUnicode value is {sys.maxunicode}.\n" \
			f"Echo statement in"


class AdicityNoFuncError(AdicityError):
	pass


class AdicityBalanceError(AdicityError):
	pass
