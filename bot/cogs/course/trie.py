from typing import Dict, Tuple, List, Optional, Iterable, Any



class Trie:
    def __init__(self) -> None:
        self.items: int = 0
        self.children: Dict[str, Trie] = {}
        self.is_word = False


    def __repr__(self) -> str:
        return repr(self.children)


    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Trie):
            return repr(self) == repr(other)
        return False


    def insert(self, word: str) -> None:
        if word == "":
            self.is_word = True
            return

        letter, word = self._shift(word)
        self.children[letter] = self.children.get(letter, Trie())
        self.children[letter].insert(word)
        self.items += 1


    def insert_all(self, words: Iterable[str]) -> None:
        for word in words:
            self.insert(word)


    def contains(self, word: str) -> bool:
        if word == "":
            return self.is_word

        if word[0] not in self.children:
            return False

        letter, word = self._shift(word)
        return self.children[letter].contains(word)


    def generate_prefix_groups(self, limit: int, *, prefix: str = "") -> List[str]:
        if self.items == 0:
            return []

        if self.items <= limit:
            return [prefix]

        categories = []
        for letter, subtree in self.children.items():
            categories += subtree.generate_prefix_groups(limit, prefix=prefix + letter)
        return categories


    def find_prefix_for(self, word: str, limit: int, *, prefix: str = "", i: int = 0) -> Optional[str]:
        if prefix == "" and i == 0 and not self.contains(word):
            return None

        if self.items <= limit:
            return prefix

        for letter, subtree in self.children.items():
            if word[i] == letter:
                return subtree.find_prefix_for(word, limit, prefix=prefix + letter, i=i + 1)


    @staticmethod
    def _shift(word: str) -> Tuple[str, str]:
        letter, *rest = word
        word = ''.join(rest)
        return letter, word
