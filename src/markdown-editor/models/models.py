from dataclasses import dataclass
from typing import Optional
from .types import TokenType, BlockType


@dataclass
class Token:
    text: str
    token_type: TokenType
    indentation: int

@dataclass
class Block:
    content: list[Token]
    block_type: Optional[BlockType] = None