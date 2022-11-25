import inject
from discord import Attachment

from .Backup import Backup
import bot.db



class AttachmentBackup(Backup[Attachment]):
    @inject.autoparams('attachmentRepository', 'mapper')
    def __init__(self, message_id: int | None, attachmentRepository: bot.db.AttachmentRepository, mapper: bot.db.AttachmentMapper) -> None:
        self.message_id = message_id
        self.attachmentRepository = attachmentRepository
        self.mapper = mapper


    async def traverseUp(self, attachment: Attachment) -> None:
        await super().traverseUp(attachment)


    async def backup(self, attachment: Attachment) -> None:
        await super().backup(attachment)
        columns = await self.mapper.map(attachment)

        tmp = list(columns)
        tmp[0] = self.message_id
        columns = tuple(tmp) # type: ignore[assignment]

        await self.attachmentRepository.insert([columns])


    async def traverseDown(self, attachment: Attachment) -> None:
        await super().traverseDown(attachment)