
class MockReturnFunc(object):
    """
    This object mocks the returns of a function
    It takes a generator and on each call returns
    the next value

    example:
        def true_once():
            yield True
            yield False


        class MockTrueFunc(object):
            def __init__(self):
                self.gen = true_once()

            def __call__(self):
                return self.gen.next()

        true_func = MockTrueFunc()
        true_func()     # True
        true_func()     # False
        true_func()     # None
        true_func()     # None
    """

    def __init__(self, gen):
        self.gen = gen()
        self.stopped = False

    def __call__(self, *args, **kwargs):
        if self.stopped:
            return None

        try:
            return next(self.gen)
        except StopIteration:
            self.stopped = True
