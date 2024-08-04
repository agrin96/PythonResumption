import dis
from types import CodeType
from Resumption.JumpPairs.Definitions import (
	Origin,
	Offsets,
	JumpPair,
	JumpName,
	OriginStore,
	Destination,
	ScanningState,
	DestinationStore,
)



class MissingOriginError(Exception):
	pass



class DuplicateDestinationsError(Exception):
	pass



class MissingDestinationError(Exception):
	pass



def load_attr_handler[T: Origin | Destination](
		store: dict[JumpName, list[T]],
		jump_name: str,
		candidate: T,
		new_offset: int,
    ) -> None:
    if jump_name in store:
        if not store[jump_name][-1].is_complete:
            # We handle the case that we did multiple chains of
            # attributes such as GOTO .done .done to have more
            # bytecode memory to work with.
            store[jump_name][-1].byte_offsets.append(new_offset)
            return
        store[jump_name].append(candidate)
    else:
        store[jump_name] = [candidate]
        store[jump_name][-1].byte_offsets.append(new_offset)




def find_jump_bytecodes(
		code: CodeType,
		current_origins: OriginStore | None = None,
		current_destinations: DestinationStore | None = None,
	) -> tuple[OriginStore, DestinationStore]:
	"""### Match pairs"""
	origin_store = current_origins if current_origins else {}
	destination_store = current_destinations if current_destinations else {}

	working_offsets: Offsets = []
	current_jump_name: JumpName | None = None
	current_line = 0

	state = ScanningState.SCANNING
	for instruction in dis.get_instructions(code, show_caches = True):
		if instruction.starts_line:
			current_line = instruction.starts_line

		match instruction.opname:
			case "FOR_ITER":
				pass
			case "LOAD_GLOBAL":
				if state != ScanningState.SCANNING:
					raise RuntimeError("I don't understand how to handle this situation")
				
				if isinstance((value := instruction.argval), str):
					if value.lower() == "goto":
						state = ScanningState.ORIGIN
						working_offsets.append(instruction.offset)
					if value.lower() == "label":
						state = ScanningState.DESTINATION
						working_offsets.append(instruction.offset)

			case "LOAD_NAME":
				# When adding a goto on the module level, it is loaded using
				# LOAD_NAME instead of LOAD_GLOBAL
				if state != ScanningState.SCANNING:
					raise RuntimeError("I don't understand how to handle this situation")
				
				if isinstance((value := instruction.argval), str):
					if value.lower() == "goto":
						state = ScanningState.ORIGIN
						working_offsets.append(instruction.offset)
					if value.lower() == "label":
						state = ScanningState.DESTINATION
						working_offsets.append(instruction.offset)

			case "LOAD_ATTR":
				if state == ScanningState.ORIGIN:
					if isinstance((value := instruction.argval), str):
						candidate = Origin(
							scope_name = code.co_name,
							filename = code.co_filename,
							line = current_line,
							byte_offsets = working_offsets.copy()
						)
						load_attr_handler(
							store = origin_store,
							jump_name = value,
							candidate = candidate,
							new_offset = instruction.offset
                        )
						working_offsets.clear()
						current_jump_name = value

				if state == ScanningState.DESTINATION:
					if isinstance((value := instruction.argval), str):
						candidate = Destination(
							scope_name = code.co_name,
							filename = code.co_filename,
							line = current_line,
							byte_offsets = working_offsets.copy()
						)
						load_attr_handler(
							store = destination_store,
							jump_name = value,
							candidate = candidate,
							new_offset = instruction.offset
                        )
						working_offsets.clear()
						current_jump_name = value

			case "POP_TOP":
				# Pop comes at the end of every block that defines one of our
				# goto or label statements
				if state == ScanningState.ORIGIN:
					assert current_jump_name, "Cannot have a missing jump Name"
					(origin_store[current_jump_name][-1]
	                    .byte_offsets
						.append(instruction.offset)
                    )
					origin_store[current_jump_name][-1].is_complete = True
				
				if state == ScanningState.DESTINATION:
					assert current_jump_name, "Cannot have a missing jump Name"
					(destination_store[current_jump_name][-1]
	                    .byte_offsets
						.append(instruction.offset)
                    )
					destination_store[current_jump_name][-1].is_complete = True

				state = ScanningState.SCANNING
	return (origin_store, destination_store)




def find_jump_pairs(code: CodeType) -> list[JumpPair]:
	"""### Summary
	Get jump pairs"""
	bytecode_sources = [code]
	for const in code.co_consts:
		if type(const).__name__ == "code":
			bytecode_sources.append(const)
	
	origin_store: OriginStore = {}
	destination_store: DestinationStore = {}
	for source in bytecode_sources:
		origin_store, destination_store = find_jump_bytecodes(
			source,
			current_origins = origin_store,
			current_destinations = destination_store
		)
	
	# Need to handle error cases figuring out where how to group valid and invalid
	# statements
	jumps: list[JumpPair] = []
	for label, origin_list in origin_store.items():
		# We pop the destinations as a test. If after iterating through all
		# origins we haven't popped all the destinations, then we have dangling
		# destinations.
		destination_list = destination_store.pop(label, None)
		if not destination_list:
			raise MissingDestinationError(F"No destination found for origin: {label}")
		
		scopes = [d.scope_name for d in destination_list]
		for scope in scopes:
			if scopes.count(scope) > 1:
				raise DuplicateDestinationsError(
					F"Scope '{scope}' has duplicate destination names: '{label}'"
				)
			
		jumps.append(
			JumpPair(
				name = label,
				origin = origin_list,
				destination = destination_list,
			)
		)

	# Check for dangling destinations
	for label, destination_list in destination_store.items():
		scope = destination_list[0].scope_name
		raise MissingOriginError(
			F"No origin found for destination '{label}' in scope {scope}")
	return jumps
