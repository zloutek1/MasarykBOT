import logging
from types import TracebackType
from typing import Optional, Type

import inject

from bot.db.utils.types import Pool, DBConnection, DBTransaction

log = logging.getLogger(__name__)


class TransactionContext:
    def __init__(self, pool: Pool) -> None:
        self.pool = pool
        self.conn: Optional[DBConnection] = None
        self._transaction: Optional[DBTransaction] = None


    async def __aenter__(self) -> "TransactionContext":
        await self._start()
        return self


    async def __aexit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc_val: Optional[BaseException],
            exc_tb: Optional[TracebackType]
    ) -> None:
        if exc_val is not None:
            await self._rollback()
            raise exc_val
        else:
            await self._commit()


    async def _start(self):
        self.conn: DBConnection = await self.pool.acquire()
        self._transaction = self.conn.transaction()
        await self._transaction.start()


    async def _commit(self):
        self._transaction = await self._transaction.commit()
        self.conn = await self.conn.close()


    async def _rollback(self):
        self._transaction = await self._transaction.rollback()
        log.error("Transaction failed, statement rolled back")
        self.conn = await self.conn.close()



class UnitOfWork:
    @inject.autoparams('pool')
    def __init__(self, pool: Pool) -> None:
        self.pool = pool


    def transaction(self) -> TransactionContext:
        return TransactionContext(self.pool)

