from enum import Enum
from dataclasses import dataclass


type LineNumber = int
type Offsets = list[int]
type JumpName = str


class ScanningState(Enum):
	ORIGIN      = "ORIGIN"
	DESTINATION = "DESTINATION"
	SCANNING    = "SCANNING"


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
class JumpPair:
	name: str
	origin: list[Origin]
	destination: list[Destination]


type OriginStore = dict[JumpName, list[Origin]]
type DestinationStore = dict[JumpName, list[Destination]]