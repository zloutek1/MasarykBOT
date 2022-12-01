import inject

from .course import CourseRepository, CourseEntity
from .student import StudentRepository, StudentEntity

REPOSITORIES = (CourseRepository, StudentRepository)
ENTITIES = (CourseEntity, StudentEntity)


def setup_injections(binder: inject.Binder) -> None:
    for repo_type in REPOSITORIES:
        binder.bind_to_constructor(repo_type, repo_type)