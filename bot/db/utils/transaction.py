import logging
from types import TracebackType
from typing import Optional, Type

import inject

from bot.db.utils.dbtypes import Pool, Record, DBConnection, DBTransaction

log = logging.getLogger(__name__)


class TransactionContext:
    def __init__(self, pool: Pool[Record], readonly: bool = False) -> None:
        self.pool = pool
        self.readonly = readonly

        self.conn: Optional[DBConnection]
        self._transaction: Optional[DBTransaction]


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


    async def _start(self) -> None:
        self.conn = await self.pool.acquire()
        self._transaction = self.conn.transaction(readonly=self.readonly)
        await self._transaction.start()


    async def _commit(self) -> None:
        assert self._transaction, "no transaction"
        assert self.conn, "no connection"
        
        await self._transaction.commit()
        await self.conn.close()
        
        self._transaction = None
        self.conn = None


    async def _rollback(self) -> None:
        assert self._transaction, "no transaction"
        assert self.conn, "no connection"
        
        await self._transaction.rollback()
        log.error("Transaction failed, statement rolled back")
        await self.conn.close()

        self._transaction = None
        self.conn = None




class UnitOfWork:
    @inject.autoparams('pool')
    def __init__(self, pool: Pool) -> None:
        self.pool = pool


    def transaction(self, readonly: bool = False) -> TransactionContext:
        return TransactionContext(self.pool, readonly)

