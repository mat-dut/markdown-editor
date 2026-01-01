class FootnoteTracker:
    def __init__(self):
        self.order = []
        self.occurrences = {}
        self.counter = 0

    def add_reference(self, ref_name: str) -> tuple[int, int]:
        if ref_name not in self.order:
            self.order.append(ref_name)

        if ref_name not in self.occurrences:
            self.occurrences[ref_name] = []

        self.counter += 1
        self.occurrences[ref_name].append(self.counter)

        return self.order.index(ref_name) + 1, self.counter