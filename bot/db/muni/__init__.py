import inject

__all__ = [
    'CourseRepository', 'CourseEntity',
    'StudentRepository', 'StudentEntity',
    'FacultyRepository', 'FacultyEntity',
    'setup_injections'
]

from .course import CourseRepository, CourseEntity
from .student import StudentRepository, StudentEntity
from .faculty import FacultyRepository, FacultyEntity

REPOSITORIES = (CourseRepository, StudentRepository, FacultyRepository)
ENTITIES = (CourseEntity, StudentEntity, FacultyEntity)


def setup_injections(binder: inject.Binder) -> None:
    for repo_type in REPOSITORIES:
        binder.bind_to_constructor(repo_type, repo_type)