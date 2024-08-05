import re
import dis
import libcst as cst
from types import CodeType
from Resumption.JumpPairs.Definitions import JumpPair, DataLoad, DataType


class Visitor(cst.CSTTransformer):
	def __init__(self, target: str):
		self._new_root = None
		self._target = target


	def on_visit(self, node: cst.CSTNode) -> bool:
		if hasattr(node, "name"):
			if node.name.value == self._target:
				self._new_root = node
				return False
		return True
	

	def on_leave(self, 
			original_node: cst.CSTNode,
			updated_node: cst.CSTNode,
		) -> cst.CSTNode | cst.RemovalSentinel | cst.FlattenSentinel[cst.CSTNode]:
		if type(original_node).__name__ == "Module":
			assert self._new_root, F"Failed to find {self._target} after traversal"
			return cst.Module(body = [self._new_root])
		return updated_node
	


def extract_code_from_frame(raw_source: str, target_name: str) -> tuple[str, int]:
	source = cst.parse_module(raw_source)
	source = source.visit(Visitor(target = target_name))
	
	tab_indents = len(source.default_indent.replace(" "*4, "\t"))
	source = source.code.replace(" "*4, "\t")
	source_lines = source.splitlines()

	# Here we remove leading and trailing empty lines because when functions are
	# nested in functions then the parser extracts them with leading and trailing
	# empty lines.
	start_index = 0
	for idx, line in enumerate(source_lines):
		if re.match(r"^\s+$|^$", line) is None:
			start_index = idx
			break

	end_index = 0
	for idx, line in enumerate(source_lines[::-1]):
		if re.match(r"^\s+$|^$", line) is None:
			end_index = len(source_lines) - idx
			break

	source = "\n".join(source_lines[start_index:end_index])
	return source, tab_indents



def patch_bytecode(code: CodeType, jump_pairs: list[JumpPair]) -> CodeType:
	bytecode_sources = [(-1,code)]
	for idx, const in enumerate(code.co_consts):
		if type(const).__name__ == "code":
			bytecode_sources.append((idx, const))

	patched_sources = []
	for idx, source in bytecode_sources:		
		instructions = list(source.co_code)
		
		for pair in jump_pairs:
			destination = pair.destination[0]
			for origin in pair.origin:
				
				if source.co_name not in (origin.scope_name, destination.scope_name):
					continue

				shift_back_data: list[DataLoad] = []
				for data in pair.data_loads:
					if origin.byte_offsets[0] < data.instructions[0].offset:
						shift_back_data.append(data)

				current_offset = origin.byte_offsets[0]
				for data in shift_back_data:
					if data.data_type == DataType.CODE:
						instructions[current_offset] = data.instructions[0].opcode
						if data.instructions[0].arg is not None:
							instructions[current_offset + 1] = data.instructions[0].arg
						
						instructions[current_offset + 2] = data.instructions[1].opcode
						if data.instructions[1].arg is not None:
							instructions[current_offset + 3] = data.instructions[1].arg

						instructions[current_offset + 4] = data.instructions[2].opcode
						if data.instructions[2].arg is not None:
							instructions[current_offset + 5] = data.instructions[2].arg
						current_offset = current_offset + 6
					
					if data.data_type in (DataType.LOCAL, DataType.GLOBAL):
						instructions[current_offset] = data.instructions[0].opcode
						if data.instructions[0].arg is not None:
							instructions[current_offset + 1] = data.instructions[0].arg

						instructions[current_offset + 2] = data.instructions[1].opcode
						if data.instructions[1].arg is not None:
							instructions[current_offset + 3] = data.instructions[1].arg
						current_offset = current_offset + 4


				# Floor divide by two because each instruction is 2 bytes so to jump
				# we need to calculate the byte position
				tunnel = (destination.byte_offsets[-1] - current_offset) // 2
				# dis.Instruction()
				if tunnel > 0:
					instructions[current_offset] = dis.opmap["JUMP_FORWARD"]
					instructions[current_offset + 1] = tunnel
				else:
					instructions[current_offset] = dis.opmap["JUMP_BACKWARD"]
					instructions[current_offset + 1] = abs(tunnel)

				current_offset = current_offset + 2
				while current_offset <= origin.byte_offsets[-1]:
					instructions[current_offset] = dis.opmap["NOP"]
					current_offset += 1

				# Fill the destination offset bytes with a NO-OP
				offsets = destination.byte_offsets
				current_offset = offsets[0]
				while current_offset <= offsets[-1]:
					instructions[current_offset] = dis.opmap["NOP"]
					current_offset += 1
		patched_sources.append((idx, bytes(instructions)))
	
	# Patch the source by replacing attributes of the code.
	new_consts = []
	for idx, const in enumerate(code.co_consts):
		if type(const).__name__ != "code":
			new_consts.append(const)
			continue

		for sidx, source in patched_sources[1:]:
			if idx == sidx:
				new_consts.append(const.replace(co_code = source))
				break

	code = code.replace(
		co_code = patched_sources[0][1],
		co_consts = tuple(new_consts)
	)

	return code


# def patch_bytecode(code: CodeType, jump_pairs: list[JumpPair]) -> CodeType:
# 	bytecode_sources = [(-1,code)]
# 	for idx, const in enumerate(code.co_consts):
# 		if type(const).__name__ == "code":
# 			bytecode_sources.append((idx, const))

# 	patched_sources = []
# 	for idx, source in bytecode_sources:		
# 		instructions = list(source.co_code)
		
# 		for pair in jump_pairs:
# 			destination = pair.destination[0]
# 			for origin in pair.origin:
				
# 				if source.co_name not in (origin.scope_name, destination.scope_name):
# 					continue

# 				# Floor divide by two because each instruction is 2 bytes so to jump
# 				# we need to calculate the byte position
# 				tunnel = (destination.byte_offsets[-1] - origin.byte_offsets[0]) // 2 
# 				offsets = origin.byte_offsets

# 				if tunnel > 0:
# 					instructions[offsets[0]] = dis.opmap["JUMP_FORWARD"]
# 					instructions[offsets[0] + 1] = tunnel
# 				else:
# 					instructions[offsets[0]] = dis.opmap["JUMP_BACKWARD"]
# 					instructions[offsets[0] + 1] = abs(tunnel)

# 				current_offset = offsets[0] + 2
# 				while current_offset <= offsets[-1]:
# 					instructions[current_offset] = dis.opmap["NOP"]
# 					current_offset += 1


# 				# Fill the destination offset bytes with a NO-OP
# 				offsets = destination.byte_offsets
# 				current_offset = offsets[0]
# 				while current_offset <= offsets[-1]:
# 					instructions[current_offset] = dis.opmap["NOP"]
# 					current_offset += 1
# 		patched_sources.append((idx, bytes(instructions)))
	
# 	# Patch the source by replacing attributes of the code.
# 	new_consts = []
# 	for idx, const in enumerate(code.co_consts):
# 		if type(const).__name__ != "code":
# 			new_consts.append(const)
# 			continue

# 		for sidx, source in patched_sources[1:]:
# 			if idx == sidx:
# 				new_consts.append(const.replace(co_code = source))
# 				break

# 	code = code.replace(
# 		co_code = patched_sources[0][1],
# 		co_consts = tuple(new_consts)
# 	)

# 	return code

