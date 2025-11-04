import argparse
import asyncio
import datetime as dt
import os
import sys
from pathlib import Path
from decimal import Decimal

# Ensure project root is on sys.path when running as a script
ROOT: Path = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from app.models.base import Base
from app.modules.finance.infrastructure.persistence.models.account import Account
from app.modules.finance.infrastructure.persistence.models.category import Category
from app.modules.finance.infrastructure.persistence.models.transaction import Transaction
from app.modules.finance.infrastructure.persistence.models.transfer import Transfer
from dotenv import load_dotenv


def parse_args():
    p = argparse.ArgumentParser(description="Diagnóstico de saldos por conta")
    p.add_argument("--year", type=int, default=None, help="Ano (UTC)")
    p.add_argument("--month", type=int, default=None, help="Mês (1-12, UTC)")
    p.add_argument("--user", type=int, default=None, help="ID do usuário para filtrar (opcional)")
    p.add_argument("--env-file", type=str, default=str(ROOT / ".env"), help="Caminho do arquivo .env (default: ./\.env)")
    return p.parse_args()


async def main():
    args = parse_args()
    # Load .env first
    load_dotenv(args.env_file)
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL não definido no ambiente.")
        return

    # Suporta URLs sync convertendo para async quando necessário
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(db_url, future=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    now = dt.datetime.now(dt.timezone.utc)
    year = args.year or now.year
    month = args.month or now.month

    async with async_session() as session:
        print(f"Diagnóstico: {year}-{month:02d} (UTC)")
        if args.user:
            print(f"Filtro user_id={args.user}")
        print("--- Accounts ---")
        q_acc = select(Account)
        if args.user:
            q_acc = q_acc.where(Account.user_id == args.user)
        accounts = (await session.execute(q_acc)).scalars().all()
        for a in accounts:
            print(f"Account id={a.id} name={a.name} currency={a.currency} status={getattr(a, 'status', 'ACTIVE')}")

        print("\n--- Recent Transfers (10) ---")
        q_tr = select(Transfer).order_by(Transfer.id.desc()).limit(10)
        if args.user:
            q_tr = q_tr.where(Transfer.user_id == args.user)
        transfers = (await session.execute(q_tr)).scalars().all()
        for t in transfers:
            print(f"Transfer id={t.id} user={t.user_id} src={t.src_account_id} dst={t.dst_account_id} src_cents={t.src_amount_cents} dst_cents={t.dst_amount_cents} when={t.occurred_at} voided={getattr(t, 'voided', False)}")

        print("\n--- Transactions in month ---")
        q_tx = (
            select(Transaction, Account, Category)
            .join(Account, Transaction.account_id == Account.id)
            .join(Category, Transaction.category_id == Category.id, isouter=True)
        )
        if args.user:
            q_tx = q_tx.where(Transaction.user_id == args.user)
        rows = (await session.execute(q_tx)).all()
        totals: dict[int, int] = {}
        for tx, acc, cat in rows:
            occ = tx.occurred_at
            if occ.tzinfo is not None:
                occ = occ.astimezone(dt.timezone.utc)
            if occ.year != year or occ.month != month:
                continue
            sign = 1
            if cat is not None and str(getattr(cat, 'type', '')).upper() == 'EXPENSE':
                sign = -1
            if bool(getattr(tx, 'voided', False)):
                continue
            totals[tx.account_id] = totals.get(tx.account_id, 0) + sign * int(tx.amount_cents)
            print(f"tx id={tx.id} acc={tx.account_id} cents={tx.amount_cents} sign={sign} type={getattr(cat, 'type', None)} transfer_id={tx.transfer_id} voided={tx.voided} when={tx.occurred_at}")

        print("\n--- Totals (cents) ---")
        for acc_id, cents in sorted(totals.items()):
            acc = next((a for a in accounts if a.id == acc_id), None)
            cur = acc.currency if acc else '??'
            print(f"account_id={acc_id} total_cents={cents} currency={cur}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
