from core.dated.repository import DatedRepository
from role.model import Role


class RoleRepository(DatedRepository[Role]):
    @property
    def model(self):
        return Role
