import inject

from __oild.bot.cogs.logger.processors._base import Backup
from src.bot import AttachmentEntity, AttachmentMapper, AttachmentRepository
from src.bot import MessageAttachment


class AttachmentBackup(Backup[MessageAttachment]):
    @inject.autoparams()
    def __init__(self, attachment_repository: AttachmentRepository, mapper: AttachmentMapper) -> None:
        super().__init__()
        self.attachment_repository = attachment_repository
        self.mapper = mapper

    async def traverse_up(self, attachment: MessageAttachment) -> None:
        await super().traverse_up(attachment)

    async def backup(self, attachment: MessageAttachment) -> None:
        entity: AttachmentEntity = await self.mapper.map(attachment)
        await self.attachment_repository.insert(entity)

    async def traverse_down(self, attachment: MessageAttachment) -> None:
        await super().traverse_down(attachment)
