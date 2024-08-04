import dis
from types import CodeType
from Resumption.JumpPairs.Definitions import JumpPair



def patch_bytecode(code: CodeType, jump_pairs: list[JumpPair]) -> CodeType:
	bytecode_sources = [(-1,code)]
	for idx, const in enumerate(code.co_consts):
		if type(const).__name__ == "code":
			bytecode_sources.append((idx, const))

	patched_sources = []
	for idx, source in bytecode_sources:		
		instructions = list(source.co_code)
		for pair in jump_pairs:
			# if source.co_name not in (pair.origin.scope_name, pair.destination.scope_name):
			# 	continue
			destination = pair.destination[0]
			for origin in pair.origin:
				if source.co_name not in (origin.scope_name, destination.scope_name):
					continue

				# Floor divide by two because each instruction is 2 bytes so to jump
				# we need to calculate the byte position
				tunnel = (destination.byte_offsets[-1] - origin.byte_offsets[0]) // 2 
				offsets = origin.byte_offsets

				if tunnel > 0:
					instructions[offsets[0]] = dis.opmap["JUMP_FORWARD"]
					instructions[offsets[0] + 1] = tunnel
				else:
					instructions[offsets[0]] = dis.opmap["JUMP_BACKWARD"]
					instructions[offsets[0] + 1] = abs(tunnel)

				current_offset = offsets[0] + 2
				while current_offset <= offsets[-1]:
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
