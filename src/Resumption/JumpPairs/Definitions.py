import dis
from enum import Enum
from dataclasses import dataclass


type LineNumber = int
type Offsets = list[int]
type JumpName = str


class ScanningState(Enum):
	ORIGIN      = "ORIGIN"
	DESTINATION = "DESTINATION"
	SCANNING    = "SCANNING"
	LOAD_CODE   = "LOAD_CODE"
	LOAD_LOCAL  = "LOAD_LOCAL"
	LOAD_GLOBAL = "LOAD_GLOBAL"


class DataType(Enum):
	CODE   = "CODE"
	LOCAL  = "LOCAL"
	GLOBAL = "GLOBAL"


@dataclass
class Origin:
	scope_name: str
	filename: str
	line: int
	byte_offsets: Offsets
	is_complete: bool = False


@dataclass
class Destination:
	scope_name: str
	filename: str
	line: int
	byte_offsets: Offsets
	is_complete: bool = False


@dataclass
class DataLoad:
	name: str | int
	scope: str
	data_type: DataType
	instructions: list[dis.Instruction]


@dataclass
class JumpPair:
	name: str
	origin: list[Origin]
	destination: list[Destination]
	data_loads: list[DataLoad]


type OriginStore = dict[JumpName, list[Origin]]
type DestinationStore = dict[JumpName, list[Destination]]
type DataStore = list[DataLoad]