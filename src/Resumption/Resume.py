import os
import dis
import shutil
from termcolor import cprint
from types import CodeType
from Resumption.BytecodePatcher.Patcher import (
	patch_bytecode,
	extract_code_from_frame,
)
from Resumption.JumpPairs.Parser import find_jump_pairs



def run_with_resumption(raw_source: str, file_name: str,debug: bool = False):
	"""### Summary
	Pass a source code string to this file to run it with resumption. We listen
	to keyboard interrupts and catch them to then resume the code from the 
	line before the interrupted line.

	Note this is not in a loop so you can only interrupt once.
	"""
	if debug:
		if os.path.exists("./debug/"):
			shutil.rmtree("./debug/")
		os.mkdir("./debug/")

	source = compile(raw_source, file_name, mode = "exec")
	if debug:
		with open("./debug/starting_source.txt", "w+") as f:
			dis.dis(source, file = f)
	
		
	source_stack: list[CodeType] = []
	try:
		cprint(F"DEBUG: Running source {file_name}", "yellow")
		exec(source, {"__builtins__": __builtins__})
	except KeyboardInterrupt as e:
		cprint("\nDEBUG: Interrupted run", "yellow")
		trace = e.__traceback__
		assert trace, "Must have a traceback."
		
		depth = 0
		while trace.tb_next:
			source_frame = trace.tb_next.tb_frame
			scope_name = source_frame.f_code.co_name

			if scope_name == "<module>":
				line_source = raw_source.splitlines()
				
				error_lineno = source_frame.f_lineno - 1
				error_line = line_source[error_lineno]
				
				error_indent = " "*(len(error_line) - len(error_line.lstrip()))
				line_source.insert(error_lineno, F"{error_indent}LABEL .recovery_{depth}")
				
				# We will not jump over the import statements because they may
				# be necessary throught the code.
				end_import_index = 0
				for idx, line in enumerate(line_source):
					if "import" in line:
						continue
					end_import_index = idx
					break
				
				line_source.insert(end_import_index, F"GOTO .recovery_{depth}")
				patched_source = "\n".join(line_source)
			else:
				# Since each frame is essentially a different scope (usually functional)
				# We can use the `extract_code_from_frame` method to pull this specific
				# function out form the whole code. This will allow us to treat the
				# source as if it was just this function.
				name = source_frame.f_code.co_name
				source, indent_level = extract_code_from_frame(raw_source, name)
				indent = "\t" * indent_level

				if debug:
					with open(F"./debug/extracted_source_before_{name}.txt", "w+") as file:
						file.write(source)

				line_source = source.splitlines()
				# We set the target of the jump to the line before the errored line
				# so we can resume running.
				
				start_offset = source_frame.f_code.co_firstlineno 
				if start_offset == 0:
					error_lineno = source_frame.f_lineno - 1
				else:
					error_lineno = source_frame.f_lineno - start_offset

				# The offending line may be nested deeper than the function such
				# as if it is in an if statement.
				error_line = line_source[error_lineno]
				error_indent = "\t"*(len(error_line) - len(error_line.lstrip()))
				line_source.insert(error_lineno, F"{error_indent}LABEL .recovery_{depth}")
				
				# We set the GOTO statement to the line right after the funcion
				# def statement so that execution of the function immediately
				# jumps over to the correct point.
				line_source.insert(1, F"{indent}GOTO .recovery_{depth}")
				patched_source = "\n".join(line_source)

				if debug:
					with open(F"./debug/extracted_source_after_{name}.txt", "w+") as file:
						file.write(patched_source)

			byte_source = compile(
				source = patched_source,
				filename = source_frame.f_code.co_filename,
				mode = "exec",
			)
			jumps = find_jump_pairs(byte_source)
			patched_source = patch_bytecode(byte_source, jump_pairs = jumps)

			# Because we recompiled only one function, python continues to treat
			# it as a module. However the first element in the co_consts tuple
			# have the bytecode for the function we actually want. So we will
			# store it and then place it in the co_consts of the rebuilt code.
			if scope_name != "<module>":
				patched_source = patched_source.co_consts[0]

			source_stack.append(patched_source)
			trace = trace.tb_next
			depth += 1

	# Begin Reassembly of code.
	revered_sources = source_stack[::-1]
	for sidx in range(0, len(revered_sources) - 1):
		current = revered_sources[sidx]
		next_source = revered_sources[sidx + 1]
		
		# Patch the source by replacing attributes of the code.
		new_consts = []
		for idx, const in enumerate(next_source.co_consts):
			if type(const).__name__ != "code":
				new_consts.append(const)
				continue
			if const.co_name == current.co_name:
				new_consts.append(const.replace(
					co_code = current.co_code,
					co_names = current.co_names
				))
				continue
			new_consts.append(const)

		revered_sources[sidx + 1] = next_source.replace(
			co_consts = tuple(new_consts),
		)

	# Resume program run
	final_source = revered_sources[-1]
	if debug:
		with open("./debug/patched_source.txt","w+") as f:
			dis.dis(final_source, file = f)

	cprint("DEBUG: Resuming code", "yellow")
	exec(final_source, {"__builtins__": __builtins__})
