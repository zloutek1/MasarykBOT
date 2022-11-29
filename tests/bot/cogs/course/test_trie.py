import unittest.mock

from assertpy import assert_that

from bot.cogs.course.trie import Trie



class TrieTests(unittest.TestCase):
    @staticmethod
    def test_insert_given_empty_word_sets_root_as_word():
        trie = Trie()
        trie.insert("")
        assert_that(trie.is_word).is_true()


    @staticmethod
    def test_insert_given_word_sets_word_as_word():
        trie = Trie()
        trie.insert("hi")

        assert_that(trie.children).contains('h')
        assert_that(trie.children['h'].is_word).is_false()

        assert_that(trie.children['h'].children).contains('i')
        assert_that(trie.children['h'].children['i'].is_word).is_true()


    @staticmethod
    def test_contains_given_existing_word_returns_true():
        trie = Trie()
        trie.insert("hi")
        assert_that(trie.contains('hi')).is_true()


    @staticmethod
    def test_contains_given_missing_word_returns_false():
        trie = Trie()
        trie.insert("hi")
        assert_that(trie.contains('hello')).is_false()


    @staticmethod
    def test_insert_all_given_two_words_inserts_both():
        multi_trie = Trie()
        multi_trie.insert_all(["hi", "hello"])

        single_trie = Trie()
        single_trie.insert("hi")
        single_trie.insert("hello")

        assert_that(single_trie).is_equal_to(multi_trie)


    @staticmethod
    def test_generate_prefix_groups_given_limit_one_returns_five_result():
        trie = Trie()
        trie.insert_all(["hello", "hi", "help", "helicopter", "hire", "hindu", "hollow", "ah"])

        actual = trie.generate_prefix_groups(1)
        assert_that(actual).contains_only("hell", "heli", "hir", "hin", "ho", "a")


    @staticmethod
    def test_generate_prefix_groups_given_limit_two_returns_five_results():
        trie = Trie()
        trie.insert_all(["hello", "hi", "help", "helicopter", "hire", "hindu", "hollow", "ah"])

        actual = trie.generate_prefix_groups(2)
        assert_that(actual).contains_only("hell", "heli", "hi", "ho", "a")


    @staticmethod
    def test_generate_prefix_groups_given_limit_three_returns_four_results():
        trie = Trie()
        trie.insert_all(["hello", "hi", "help", "helicopter", "hire", "hindu", "hollow", "ah"])

        actual = trie.generate_prefix_groups(3)
        assert_that(actual).contains_only("he", "hi", "ho", "a")


    @staticmethod
    def test_generate_prefix_groups_given_limit_seven_returns_two_results():
        trie = Trie()
        trie.insert_all(["hello", "hi", "help", "helicopter", "hire", "hindu", "hollow", "ah"])

        actual = trie.generate_prefix_groups(7)
        assert_that(actual).contains_only("h", "a")


    @staticmethod
    def test_find_prefix_with_missing_word_returns_None():
        trie = Trie()
        trie.insert_all(["hello", "hi", "help", "helicopter", "hire", "hindu", "hollow", "ah"])

        actual = trie.find_prefix_for("alibaba", limit=3)
        assert_that(actual).is_none()


    @staticmethod
    def test_find_prefix_for_given_limit_three_returns_correct_prefix():
        trie = Trie()
        trie.insert_all(["hello", "hi", "help", "helicopter", "hire", "hindu", "hollow", "ah"])

        actual = trie.find_prefix_for("hello", limit=3)
        assert_that(actual).is_equal_to("he")


