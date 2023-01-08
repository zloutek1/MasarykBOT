import logging

log = logging.getLogger(__name__)



class ProgressReporter:
    def __init__(self, max_count: int, report_percentage: int = 5, start_count: int = 0, message: str = 'Progress: %d') -> None:
        self.max_count = max_count
        self.report_percentage = report_percentage
        self.count = start_count
        self.message = message


    @property
    def percentage(self) -> float:
        return self.count / self.max_count * 100


    def increment(self, by: int = 1) -> None:
        prev_percentage = self.percentage
        self.count += by

        if self._should_report(prev_percentage):
            self._report_progress()


    def _should_report(self, prev_percentage: float) -> bool:
        return prev_percentage % self.report_percentage > self.percentage % self.report_percentage

    def _report_progress(self) -> None:
        log.info(self.message, self.percentage)
