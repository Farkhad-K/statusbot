import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class ServiceConfig:
    dsn: str
    table: str


@dataclass
class Config:
    token: str
    allowed_ids: list[int]
    q1: ServiceConfig
    q2: ServiceConfig
    k: ServiceConfig


def load_config() -> Config:
    token = os.environ.get("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("BOT_TOKEN is required in .env")

    allowed_raw = os.environ.get("ALLOWED_IDS", "").strip()
    allowed_ids = [int(uid) for uid in allowed_raw.split(",") if uid.strip()]

    def svc(prefix: str) -> ServiceConfig:
        dsn   = os.environ.get(f"{prefix}_DSN", "").strip()
        table = os.environ.get(f"{prefix}_TABLE", "").strip()
        if not dsn or not table:
            raise RuntimeError(f"{prefix}_DSN and {prefix}_TABLE are required in .env")
        return ServiceConfig(dsn=dsn, table=table)

    return Config(
        token=token,
        allowed_ids=allowed_ids,
        q1=svc("Q1"),
        q2=svc("Q2"),
        k=svc("K"),
    )
