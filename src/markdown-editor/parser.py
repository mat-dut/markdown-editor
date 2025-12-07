from models.models import Token, Block
from models.types import TokenType, BlockType

def handle_heading(current_block: Block, token: Token) -> Block:
    current_block.content.append(token)
    current_block.block_type = BlockType.HEADING

    return current_block

def handle_text(current_block: Block, token: Token) -> Block:
    if current_block.block_type in [BlockType.ORDERED_LIST, BlockType.UNORDERED_LIST]:
        current_block.content[-1].text += f" {token.text}"
    else:
        current_block.content.append(token)
        current_block.block_type = BlockType.PARAGRAPH

    return current_block

def handle_blockquote(current_block: Block, token: Token, blocks: list[Block]) -> Block:
  if current_block.block_type != BlockType.BLOCKQUOTE:
      if current_block.content:
          blocks.append(current_block)
      return Block(content=[token], block_type=BlockType.BLOCKQUOTE)
  else:
      current_block.content.append(token)
      return current_block

def handle_list_item(current_block: Block, token: Token, blocks: list[Block]) -> Block:
    if token.token_type == TokenType.ORDERED_LIST_ITEM and current_block.block_type == BlockType.UNORDERED_LIST:
        blocks.append(current_block)
        return Block(content=[token], block_type=BlockType.ORDERED_LIST)

    elif token.token_type == TokenType.UNORDERED_LIST_ITEM and current_block.block_type == BlockType.ORDERED_LIST:
        blocks.append(current_block)
        return Block(content=[token], block_type=BlockType.UNORDERED_LIST)

    else:
        current_block.content.append(token)
        current_block.block_type = BlockType.ORDERED_LIST if token.token_type == TokenType.ORDERED_LIST_ITEM else BlockType.UNORDERED_LIST
        return current_block

def handle_code(current_block: Block, token: Token, blocks: list[Block]) -> Block:
    if current_block.block_type == BlockType.CODE:
        current_block.content.append(token)
        blocks.append(current_block)
        return Block(content=[])

    if current_block.content:
        blocks.append(current_block)

    return Block(content=[token], block_type=BlockType.CODE)


def parse_blocks(tokens: list[Token]) -> list[Block]:

    blocks: list[Block] = []

    current_block: Block = Block(content=[])

    for token in tokens:
        if current_block.block_type == BlockType.CODE and token.token_type != TokenType.CODE:
            current_block.content.append(token)
            continue

        elif token.token_type == TokenType.HEADING:
            current_block = handle_heading(current_block, token)

            blocks.append(current_block)

            current_block = Block(content=[])

        elif token.token_type == TokenType.TEXT:
            current_block = handle_text(current_block, token)

        elif token.token_type == TokenType.CODE:
            current_block = handle_code(current_block, token, blocks)

        elif token.token_type == TokenType.UNORDERED_LIST_ITEM or token.token_type == TokenType.ORDERED_LIST_ITEM:
            current_block = handle_list_item(current_block, token, blocks)

        elif token.token_type == TokenType.BLANK_LINE:
            if current_block.content:
                blocks.append(current_block)

            current_block = Block(content=[])

        elif token.token_type == TokenType.HORIZONTAL_RULE:
            if current_block.content:
                blocks.append(current_block)
                current_block = Block(content=[])

            blocks.append(Block(content=[token], block_type=BlockType.HORIZONTAL_RULE))

        elif token.token_type == TokenType.EOF:
            if current_block.content:
                blocks.append(current_block)
            current_block = Block(content=[])

    return blocks