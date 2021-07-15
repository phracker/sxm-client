from enum import Enum

class RegionChoice(str, Enum):
    US: str
    CA: str

def main(username: str = ..., password: str = ..., do_list: bool = ..., port: int = ..., host: str = ..., verbose: bool = ..., region: RegionChoice = ...) -> int: ...
