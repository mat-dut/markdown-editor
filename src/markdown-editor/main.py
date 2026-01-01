from lexer import tokenize
from parser import parse_blocks
from renderer import render_html

def main():
    with open("examples/table.md", "r") as file:
        tokens = tokenize(file.read())
        blocks = parse_blocks(tokens)
        html = render_html(blocks)

        for token in tokens:
            print(token)

        print("\n")

        for block in blocks:
            print(block)

        print("\n")

        print(html)


if __name__ == "__main__":
    main()
