import os
import sys
import datetime as dt
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import argparse
import asyncio

import httpx
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def parse_args():
    p = argparse.ArgumentParser(description="Import FX rates from ExchangeRate-API into fx_rates table")
    p.add_argument("--date", type=str, default=None, help="YYYY-MM-DD (defaults to today UTC)")
    p.add_argument("--env-file", type=str, default=str(ROOT / ".env"))
    return p.parse_args()


async def upsert_rate(session: AsyncSession, *, d: dt.date, base: str, quote: str, value: Decimal):
    # Ensure fixed precision 18,10
    v = value.quantize(Decimal(1).scaleb(-10), rounding=ROUND_HALF_UP)
    sql = text(
        """
        INSERT INTO fx_rates (date, base, quote, rate_value)
        VALUES (:date, :base, :quote, :rate)
        ON CONFLICT (date, base, quote) DO UPDATE SET rate_value = EXCLUDED.rate_value, updated_at = CURRENT_TIMESTAMP
        """
    )
    await session.execute(sql, {"date": d, "base": base, "quote": quote, "rate": str(v)})


async def main():
    args = parse_args()
    load_dotenv(args.env_file)

    api_key = os.getenv("EXR_API_KEY")
    if not api_key:
        print("EXR_API_KEY not set")
        sys.exit(1)
    bases = (os.getenv("EXR_BASES") or "EUR").split(",")
    quotes = (os.getenv("EXR_QUOTES") or "BRL").split(",")
    url_base = os.getenv("EXR_URL_BASE") or "https://v6.exchangerate-api.com/v6"

    # DB URL
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not set")
        sys.exit(1)
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)

    # Date handling
    today = dt.datetime.now(dt.timezone.utc).date()
    if args.date:
        try:
            d = dt.date.fromisoformat(args.date)
        except Exception:
            print("Invalid --date; use YYYY-MM-DD")
            sys.exit(1)
    else:
        d = today

    engine = create_async_engine(db_url, future=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session() as session:
        async with httpx.AsyncClient(timeout=30.0) as client:
            for base in [b.strip().upper() for b in bases if b.strip()]:
                # Use latest endpoint; assume run on the day of interest
                url = f"{url_base}/{api_key}/latest/{base}"
                r = await client.get(url)
                r.raise_for_status()
                data = r.json()
                conv = data.get("conversion_rates") or {}
                # Persist selected quotes and inverses
                for q in [q.strip().upper() for q in quotes if q.strip()]:
                    if q == base:
                        continue
                    rate = conv.get(q)
                    if rate is None:
                        print(f"missing quote {q} for base {base}")
                        continue
                    rate_dec = Decimal(str(rate))
                    await upsert_rate(session, d=d, base=base, quote=q, value=rate_dec)
                    inv = Decimal("1") / rate_dec
                    await upsert_rate(session, d=d, base=q, quote=base, value=inv)
        await session.commit()

    await engine.dispose()
    print(f"Imported {bases} -> {quotes} for date {d}")


if __name__ == "__main__":
    asyncio.run(main())

