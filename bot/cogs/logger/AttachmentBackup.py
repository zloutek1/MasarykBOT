import inject
from discord import Attachment

from .Backup import Backup
import bot.db


class AttachmentBackup(Backup[Attachment]):
    @inject.autoparams('attachment_repository', 'mapper')
    def __init__(self, message_id: int | None, attachment_repository: bot.db.AttachmentRepository,
                 mapper: bot.db.AttachmentMapper) -> None:
        self.message_id = message_id
        self.attachment_repository = attachment_repository
        self.mapper = mapper

    async def traverse_up(self, attachment: Attachment) -> None:
        await super().traverse_up(attachment)

    async def backup(self, attachment: Attachment) -> None:
        await super().backup(attachment)
        columns = await self.mapper.map(attachment)

        tmp = list(columns)
        tmp[0] = self.message_id
        columns = tuple(tmp)  # type: ignore[assignment]

        await self.attachment_repository.insert([columns])

    async def traverse_down(self, attachment: Attachment) -> None:
        await super().traverse_down(attachment)
