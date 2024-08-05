from Resumption import (
	run_with_resumption
)

with open("./src/test_source.py", "r") as file:
	run_with_resumption(raw_source = file.read(), file_name = "test_source.py")