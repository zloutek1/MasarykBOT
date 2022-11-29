import unittest.mock

from bot.cogs.course.trie import Trie



class TrieTests(unittest.TestCase):
    def test_insert_given_empty_word_sets_root_as_word(self):
        trie = Trie()
        trie.insert("")
        self.assertTrue(trie.is_word)


    def test_insert_given_word_sets_word_as_word(self):
        trie = Trie()
        trie.insert("hi")

        self.assertIn('h', trie.children)
        self.assertFalse(trie.children['h'].is_word)

        self.assertIn('i', trie.children['h'].children)
        self.assertTrue(trie.children['h'].children['i'].is_word)


    def test_contains_given_existing_word_returns_true(self):
        trie = Trie()
        trie.insert("hi")

        self.assertTrue(trie.contains('hi'))


    def test_contains_given_missing_word_returns_false(self):
        trie = Trie()
        trie.insert("hi")

        self.assertFalse(trie.contains('hello'))


    def test_insert_all_given_two_words_inserts_both(self):
        multi_trie = Trie()
        multi_trie.insert_all(["hi", "hello"])

        single_trie = Trie()
        single_trie.insert("hi")
        single_trie.insert("hello")

        self.assertEqual(single_trie, multi_trie)


    def test_generate_prefix_groups_given_limit_one_returns_five_result(self):
        trie = Trie()
        trie.insert_all(["hello", "hi", "help", "helicopter", "hire", "hindu", "hollow", "ah"])

        actual = trie.generate_prefix_groups(1)
        self.assertEqual(["hell", "heli", "hir", "hin", "ho", "a"], actual)


    def test_generate_prefix_groups_given_limit_two_returns_five_results(self):
        trie = Trie()
        trie.insert_all(["hello", "hi", "help", "helicopter", "hire", "hindu", "hollow", "ah"])

        actual = trie.generate_prefix_groups(2)
        self.assertEqual(["hell", "heli", "hi", "ho", "a"], actual)


    def test_generate_prefix_groups_given_limit_three_returns_four_results(self):
        trie = Trie()
        trie.insert_all(["hello", "hi", "help", "helicopter", "hire", "hindu", "hollow", "ah"])

        actual = trie.generate_prefix_groups(3)
        self.assertEqual(["he", "hi", "ho", "a"], actual)


    def test_generate_prefix_groups_given_limit_seven_returns_two_results(self):
        trie = Trie()
        trie.insert_all(["hello", "hi", "help", "helicopter", "hire", "hindu", "hollow", "ah"])

        actual = trie.generate_prefix_groups(7)
        self.assertEqual(["h", "a"], actual)


    def test_find_prefix_with_missing_word_returns_None(self):
        trie = Trie()
        trie.insert_all(["hello", "hi", "help", "helicopter", "hire", "hindu", "hollow", "ah"])

        actual = trie.find_prefix_for("alibaba", limit=3)
        self.assertIsNone(actual)


    def test_find_prefix_for_given_limit_three_returns_correct_prefix(self):
        trie = Trie()
        trie.insert_all(["hello", "hi", "help", "helicopter", "hire", "hindu", "hollow", "ah"])

        actual = trie.find_prefix_for("hello", limit=3)
        self.assertEqual("he", actual)


