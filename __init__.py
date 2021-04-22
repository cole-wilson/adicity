"""
Docstring...
"""
import time
import logging
import re
import sys
import colorama
import datetime
import inspect
from adicity import errors, debugger


colorama.init()
LOG_LEVEL = logging.FATAL
logging.basicConfig(encoding='utf-8', level=LOG_LEVEL)
node_template: str = """
{sep}<details {state} class='tree_node' id='node_{eyedee}'>
{sep}	<summary class='token' id='token_{eyedee}' data-position='{pos}' data-end='{end}' title='{description}'>
{sep}		{self}{valuetext}
{sep}	</summary>
{sep}	<div class='tree-content'>
{content}
{sep}	</div>
{sep}</details>
"""
single_template: str = """
{sep}<span class='token' id='token_{eyedee}' data-position='{pos}' data-end='{end}' title='{description}'>
{sep}	{self}{valuetext}
{sep}</span><br>
"""
docs_template: str = """
	<li>
		<span class='op-name'>{self.name}</span>
		<p class='op-description'>{self.__doc__}</p>
	</li>
"""
parsedepth: int = -1
blocklevel: int = 0
lookingfor: str = []
Pointer: int = 0x706f696e746572
__version__: str = "0.5.0"


def _copyright():
	print(f'Adicity v{__version__}\n(c) Cole Wilson {datetime.date.today().year}, MIT License')
	return True


class TokenPrototype:
	pattern = r""
	name = None
	arg_num = -1
	flags = []
	namespace = []

	def __init__(self, **kwargs):
		for key in kwargs:
			if kwargs[key] is not None:
				self.__setattr__(key, kwargs[key])
		logging.debug(f'New TokenProtoype: {self}')

	def __repr__(self):
		return f"<{type(self).__name__}: {self.name} (r'{self.pattern}', {','.join(self.namespace)}) " \
			   f"args: {self.arg_num}>"

	def func(self):
		raise errors.AdicityNoFuncError(self)


class Token:
	capture = ""
	position = -1
	arg_num = -1
	treedepth = -1
	endpos = 0
	args = []
	vars = {}
	output = None
	name = None

	def __getitem__(self, item):
		return self.args[item - 1]

	def get_desc(self):
		return self.func.__doc__

	def get_pretty(self):
		sep = "	" * (self.treedepth + 1)
		if self.arg_num == 0:
			return self.capture
		out = self.capture + ("(" if self.name != "PROGRAM" else "")
		for c, i in enumerate(self.args):
			if i.arg_num > 2:
				out += "{\n" + i.get_pretty() + "\n}"
			elif c < self.arg_num - 1:
				out += i.get_pretty() + ", "
			else:
				out += i.get_pretty()

		out += ")"
		return out

	def get_HTML(self):
		treedepth = self.treedepth
		sep = "	" * (treedepth + 1)
		state = "closed"
		if self.name == "PROGRAM":
			state = "open"
		valuetext = f"<span class='tree-value'> --> {self.output}</span>" if self.output is not None else ""
		data = {
			"sep": sep,
			"state": state,
			"eyedee": id(self),
			"pos": self.position,
			"end": self.endpos,
			"description": self.func.__doc__,
			"self": self,
			"valuetext": valuetext,
		}
		if len(self.args) != 0:
			content = ""
			for arg in self.args:
				content += arg.get_HTML()
			return node_template.format(**data, content=content)
		else:
			return single_template.format(**data, content="")

	def pretty(self):
		sep = (self.treedepth+1) * "|   "
		out = f"{sep}{self}{(' --> '+str(self.output)) if self.output is not None else ''}\n"
		for i in self:
			out += f"{i.pretty()}"
		return out

	def print(self):
		print(self.pretty())

	def func(self, *args):
		raise errors.AdicityNoFuncError(self)

	@staticmethod
	def coerce(value):
		# if isinstance(value, arrays.Array):
		# 	return value
		# else:
		# 	return arrays.Array(value)
		return value

	def _set(self, value):
		self.output = value

	def __call__(self):
		# if __debug__:
		# 	print('Called:', self)
		if debugger.on:
			debugger.update(self)
			if str(id(self)) in debugger.breakpoints or self.name == "BREAKPOINT":
				debugger.pause()
			if debugger.broke and self.treedepth <= debugger.level:
				debugger.pause()
			time.sleep(debugger.delay)
			while not debugger.go:
				time.sleep(debugger.delay)
		try:
			result = self.func(self)
		except RecursionError:
			raise errors.AdicityRecursionError(self)
		except TypeError:
			return errors.AdicityTypeError(self)
		if result is None:
			result = 0
		self.output = self.coerce(result)
		return self.output

	def __repr__(self):
		return f"{self.name} ({self.capture})"  # + f" [{id(self)}]"

	def __iter__(self):
		return iter(self.args)

	def __init__(self, char, name, pos, arg_num, func, line=0, linepos=0, coerce=None):
		self.capture = char
		if coerce is not None:
			self.coerce = coerce
		self.name = name
		self.position = pos + 1
		self.line = line + 1
		self.linepos = linepos + 1
		self.arg_num = arg_num
		self.func = func


class Adicity:
	protos = []
	name = 'Unnamed'
	variables = {}
	typecoercion = lambda s, i: i

	def __init__(self, name):
		self.name = name

	def __iter__(self):
		return iter(self.protos)

	def __repr__(self):
		out = f'{type(self).__name__}: {self.name}\n\t{len(self.protos)} Tokens'
		for token in self.protos:
			out += f"\n\t\t -> {token}"
		# out += f"\n\t{len(self.errors)} Custom Errors"
		# for error in self.errors:
		# 	out += f"\n\t\t -> {error}"
		return out

	def totype(self, func):
		self.typecoercion = func

	def get_token_pattern(self, name):
		out = []
		for i in self.protos:
			if i.name == name:
				if re.match(r"^@.*?@$", i.pattern) and i.pattern.count('@') == 2:
					token_name = re.findall('^@(.*?)@$', i.pattern)[0]
					i.pattern = self.get_token_pattern(token_name)
				out.append(i.pattern)
		out = f'{"|".join(out)}'
		# input(out)
		return out

	def token(self, pattern: str, *namespace, end=None, custom_name=False, add=True, args=None, re_flags=[re.M]):
		if len(namespace) == 0:
			namespace = ['default']
		if re.match(r"^@.*?@$", pattern) and pattern.count('@')==2:
			token_name = re.findall('^@(.*?)@$', pattern)[0]
			pattern = self.get_token_pattern(token_name)
		def _decorator(func):
			if custom_name is False:
				name = func.__name__
			else:
				name = custom_name
			argument_names = list(inspect.signature(func).parameters.keys())
			argvalues = []

			def _actual(fakeself: Token):
				argvalues = []
				index = 1
				for i in argument_names:
					if i == 'self':
						argvalues.append(fakeself)
					elif i in func.__annotations__ and func.__annotations__[i] == Pointer:
						argvalues.append(fakeself[index])
						index += 1
					else:
						argvalues.append(fakeself[index]())
						index += 1
				return func(*argvalues)
			argnum = args or len(argument_names) - argument_names.count('self')
			newtoken = TokenPrototype(
				pattern=pattern,
				name=("START_" if end is not None else "")+name,
				arg_num=argnum,
				namespace=namespace,
				func=_actual,
				flags=re_flags
			)
			if add:
				self.protos.append(newtoken)
			if end is not None:
				self.protos.append(TokenPrototype(
					pattern=end,
					name="END_"+name,
					arg_num=0,
					func=lambda: None,
					namespace=[],
					flags=re_flags
				))
			return func
		return _decorator

	op = operation = tok = tk = token

	def namespacesep(self, pattern: str, re_flags: list = []):
		self.protos.append(TokenPrototype(
			pattern=pattern,
			name="NAMESPACE_CHANGE",
			arg_num=0,
			namespace=[],
			func=lambda: None,
			flags=re_flags
		))

	def tokenize(self, code, start=0, lineno=0, linepos=0, already=[]):
		position = 0
		lexed = []
		namespace = 'default'
		while position < len(code):
			match = None
			for token_proto in filter(lambda proto: proto.name not in already, self):
				pattern, tag, arguments, func = self.parse_parsegroup(token_proto.pattern), token_proto.name, token_proto.arg_num, token_proto.func
				is_parsegroup = '@' in token_proto.pattern
				regex = re.compile(pattern, *token_proto.flags)
				match = regex.match(code, position)
				namespacegood = (namespace in token_proto.namespace or token_proto.namespace == [])
				if match and namespacegood and len(match.group(0)) > 0:
					text = regex.findall(match.group(0))
					if len(text) == 1:
						text = text[0]
					if is_parsegroup:
						newtext = []
						for i in filter(lambda b: b != '', text):
							newtokens = self.tokenize(i, start=position, lineno=lineno, linepos=linepos,
													  already=[*already, tag])
							newtokens = newtokens[0] if len(newtokens) == 1 else newtokens
							newtext.append(newtokens)
						text = tuple(newtext)
					if token_proto.name == 'NAMESPACE_CHANGE':
						namespace = text
					elif tag:
						lexed.append(Token(
							text,
							tag,
							position,
							arguments,
							func,
							line=lineno,
							linepos=linepos,
							coerce=self.typecoercion
						))
					elif code[position] == '\n':
						lineno += 1
						linepos = 0
					break
			if not (match and namespacegood and len(match.group(0)) > 0):
				raise errors.AdicityTokenError(
					Token(code[position], '<unknown>', position, 0, None, line=lineno, linepos=linepos),
					namespace
				)
			else:
				position = match.end()
				linepos += position - match.start()
		return lexed

	@staticmethod
	def parse(tokens):
		def _parse(start_token, remaining):
			global parsedepth
			global blocklevel
			global lookingfor
			parsedepth += 1
			start_token.treedepth = parsedepth
			start_token.args = []
			if "START_" in start_token.name:
				start_token.arg_num = 999999999
				lookingfor.append(start_token.name.replace("START_", 'END_'))
			if "END_" in start_token.name:
				return False, remaining[:]
			close = 0
			for arg_num in range(start_token.arg_num):
				try:
					if len(lookingfor) != 0 and remaining[0].name == lookingfor[-1]:
						close = 1
						lookingfor.pop(-1)
						break
					newtoken, remaining = _parse(remaining[0], remaining[1:])
				except IndexError:
					raise errors.AdicityEOFError(start_token)
				if not newtoken:
					raise errors.AdicityBalanceError(lookingfor)
				try:
					newtoken.endpos = remaining[0].position - 1
				except IndexError:
					newtoken.endpos = newtoken.position
				if "START_" in newtoken.name:
					newtoken.arg_num = len(newtoken.args)
					newtoken.name = newtoken.name.replace("START_", '')
				start_token.args.append(newtoken)
			parsedepth -= 1
			return start_token, remaining[close:]

		def _run(self):
			out = 0
			for i in self:
				out = i()
			return out

		program = Token("", "PROGRAM", -1, -1, _run)
		program.args = []
		while len(tokens) > 0:
			token, tokens = _parse(tokens[0], tokens[1:])
			try:
				token.endpos = tokens[0].position + 1
			except IndexError:
				token.endpos = token.position
			if token:
				if "START" in token.name:
					token.arg_num = len(token.args)
					token.name = token.name.replace("START_", '')
				program.args.append(token)
		program.arg_num = len(program.args)
		return program

	def parse_parsegroup(self, regex, capture=True):
		for i in re.findall('@(.*?)@', regex):
			t = self.parse_parsegroup(
				self.get_token_pattern(i),
				capture=False
			).replace('(', '').replace(')', '')
			regex = regex.replace(f'@{i}@', f"({t})" if capture else t, 1)
		return regex

	def run(self, code, output=sys.stdout, error=None, inp=None):
		try:
			tokenized = self.tokenize(code)
			program = self.parse(tokenized)
			return program()
		except errors.AdicityError as err:
			sys.stderr.write(err.pretty(code))
			sys.exit(err.errorcode)

	class Writer:
		@staticmethod
		def write(text):
			return sys.stdout.write(colorama.Fore.RED + text + colorama.Fore.RESET + "\n")

	def repl(self, output=sys.stdout, error=None, inp=None):
		# Store default IO
		_original_out = sys.stdout
		_original_error = sys.stderr
		_original_inp = input

		# Add custom IO
		sys.stdout = output
		sys.stderr = self.Writer if error is None else error
		__builtins__['input'] = input if inp is None else inp

		# Print header
		date = datetime.date.today()
		_time = datetime.datetime.now()
		print(f'{self.name} repl, running on {sys.platform} at {_time}\n[Adicity v{__version__}]')
		print(f'type .quit to exit\n')

		# Mainloop
		try:
			while True:
				i = input(f'>>> ')
				if i == '.quit':
					break
				while True:
					if i.count('(') > i.count(')') or \
							i.count('[') > i.count(']') or \
							i.count('{') > i.count('}') or \
							i.count("'") % 2 != 0:
						newi = input('... ')
						i += newi + "\n"
						if newi == "":
							break
					else:
						break
				try:
					if i != "":
						out = self.run(i)
					else:
						out = None
				except SystemExit:
					out = None
				if out is not None:
					print(colorama.Fore.BLUE + '<<< ' + str(out) + colorama.Fore.RESET)
		except KeyboardInterrupt:
			pass

		# Restore default IO
		sys.stdout = _original_out
		sys.stderr = _original_error
		__builtins__['input'] = _original_inp

	def ignore(self, pattern: str):
		newtoken = TokenPrototype(
			pattern=pattern,
			name=None,
			arg_num=-1,
			func=lambda: None
		)
		self.protos.append(newtoken)
		return newtoken

	def setvar(self, key, value):
		if isinstance(key, Token):
			key = key.capture
		self.variables[key] = value
		return self.variables[key]

	def getvar(self, key):
		try:
			return self.variables[key]
		except KeyError:
			return None

	def make_docs(self):
		out = "<ul>\n"
		for i in self:
			if i.name is not None:
				out += docs_template.format(self=i)
		out += "</ul>"
		return out
