from Resumption import (
    patch_bytecode,
    find_jump_pairs,
)

def main():
	with open("./src/test.py", "r") as file:
		source = file.read()
		bytesource = compile(source, "test3.py", mode = "exec")
		# source_lines = bytesource.co_code
		dis.dis(bytesource)
		result = find_jump_pairs(code = bytesource)
		print(result)
		# return

		patched_code = patch_bytecode(code = bytesource, jump_pairs = result)
		# print(patched_code.co_consts)
		with open("./src/test5_patched_bytecode.txt", "w+") as file:
			dis.dis(patched_code, file = file)
		# exec(patched_code)

if __name__ == "__main__":
    main()