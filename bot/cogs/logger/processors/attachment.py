import inject
from discord import Attachment

from bot.db import AttachmentEntity, AttachmentMapper, AttachmentRepository
from ._base import Backup
import bot.db


class AttachmentBackup(Backup[Attachment]):
    @inject.autoparams('attachment_repository', 'mapper')
    def __init__(self, message_id: int | None, attachment_repository: AttachmentRepository,
                 mapper: AttachmentMapper) -> None:
        self.message_id = message_id
        self.attachment_repository = attachment_repository
        self.mapper = mapper

    async def traverse_up(self, attachment: Attachment) -> None:
        await super().traverse_up(attachment)

    async def backup(self, attachment: Attachment) -> None:
        await super().backup(attachment)

        entity: AttachmentEntity = await self.mapper.map(attachment)
        entity.message_id = self.message_id

        await self.attachment_repository.insert([entity])

    async def traverse_down(self, attachment: Attachment) -> None:
        await super().traverse_down(attachment)
