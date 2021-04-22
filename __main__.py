import sys
import adicity
import os

def main():
	args = sys.argv[1:]
	try:
		name = args[0]
	except IndexError:
		sys.stderr.write(f'Provide a language path: adicity <language>')
		sys.exit(104)
	cname = name.split('.')[0]
	try:
		language = __import__(name)
	except ModuleNotFoundError:
		sys.stderr.write(f'{name} language was not found. Please ensure it is a valid module name.')
		sys.exit(101)
	if type(language) is not adicity.Adicity:
		try:
			language = getattr(language, cname.title())
		except AttributeError:
			try:
				language = getattr(language, cname)
			except AttributeError:
				sys.stderr.write(f'Neither `{cname}` nor `{cname.title()}` was found in module {name}. '
									f'Please provide an absolute path.')
				sys.exit(102)
	if type(language) is not adicity.Adicity:
		sys.stderr.write(f'Language object in module is not of type Adicity!')
		sys.exit(105)
	t = "run"
	c = ""
	if len(args) == 1:
		language.repl()
	elif '-c' in args:
		c = args[args.index('-c') + 1]
	elif '--command' in args:
		c = args[args.index('--command') + 1]
	else:
		if os.path.isfile(args[1]):
			with open(args[1]) as file:
				c = file.read()
		else:
			sys.stderr.write(f'{args[1]} script was not found.')
			sys.exit(103)
	if '-d' in args or '--debug' in args:
		t = "debug"
	out = getattr(language, t)(c)


if __name__ == '__main__':
	main()
