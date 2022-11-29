import inject

from .course import CourseRepository
from .student import StudentRepository

REPOSITORIES = (CourseRepository, StudentRepository)


def setup_injections(binder: inject.Binder) -> None:
    for repo_type in REPOSITORIES:
        binder.bind_to_constructor(repo_type, repo_type)