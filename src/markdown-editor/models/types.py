from enum import Enum

class TokenType(Enum):
    HEADING = "heading"
    TEXT = "text"
    PARAGRAPH = "paragraph"
    BLANK_LINE = "blank_line"
    UNORDERED_LIST_ITEM = "unordered_list_item"
    ORDERED_LIST_ITEM = "ordered_list_item"
    HORIZONTAL_RULE = "horizontal_rule"
    EOF = "eof"

class BlockType(Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    UNORDERED_LIST = "unordered_list"
    ORDERED_LIST = "ordered_list"
    HORIZONTAL_RULE = "horizontal_rule"
