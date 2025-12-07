from models.models import Token
from models.types import TokenType
import re

def tokenize(text: str) -> list[Token]:
    lines: list[str] = text.split("\n")

    tokens: list[Token] = []

    for index, line in enumerate(lines):

        indentation = len(line) - len(line.lstrip(" \t"))

        line_stripped = line.lstrip()

        if re.match(r'^#{1,6}\s+', line_stripped):
            tokens.append(Token(text = line, token_type=TokenType.HEADING, indentation=indentation))
        elif line_stripped.startswith("---"):
            tokens.append(Token(text=line, token_type=TokenType.HORIZONTAL_RULE, indentation=indentation))
        elif line_stripped.startswith("-"):
            tokens.append(Token(text = line, token_type=TokenType.UNORDERED_LIST_ITEM, indentation=indentation))
        elif re.match(r'^\s*\d+\.\s', line_stripped):
            tokens.append(Token(text = line, token_type=TokenType.ORDERED_LIST_ITEM, indentation=indentation))
        elif line_stripped.startswith(">"):
            tokens.append(Token(text = line, token_type=TokenType.BLOCKQUOTE, indentation=indentation))
        elif line_stripped.startswith("```"):
            tokens.append(Token(text = line, token_type=TokenType.CODE, indentation=indentation))
        elif line_stripped:
            tokens.append(Token(text = line, token_type=TokenType.TEXT, indentation=indentation))
        else:
            tokens.append(Token(text = line, token_type=TokenType.BLANK_LINE, indentation=indentation))

        if index == len(lines) - 1:
            tokens.append(Token(text = "", token_type=TokenType.EOF, indentation=indentation))

    return tokens