#!/usr/bin/env python3
import argparse
import getpass
import re
import sys
from datetime import date
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv

load_dotenv(BACKEND_DIR / ".env")

from app.core.security import hash_password
from app.database.session_db import SessionLocal
from app.models.user import User
from app.schemes.users import validate_birthday
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

USERNAME_RE = re.compile(r"^[a-zA-Z]{5,32}$")


def _prompt(label: str) -> str:
    return input(f"{label}: ").strip()


def _prompt_password() -> str:
    password = getpass.getpass("Пароль: ")
    repeated = getpass.getpass("Повторите пароль: ")
    if password != repeated:
        raise ValueError("пароли не совпадают")
    return password


def _validate_username(value: str) -> str:
    if not USERNAME_RE.fullmatch(value):
        raise ValueError(
            "username должен содержать только латинские буквы (5-32 символа)"
        )
    return value


def _validate_password(value: str) -> str:
    if len(value) < 8:
        raise ValueError("пароль должен содержать минимум 8 символов")
    if len(value) > 128:
        raise ValueError("пароль должен содержать не более 128 символов")
    if any(char.isspace() for char in value):
        raise ValueError("пароль не должен содержать пробелы")
    return value


def _validate_name(label: str, value: str, *, required: bool) -> str | None:
    value = value.strip()
    if not value:
        if required:
            raise ValueError(f"{label} не может быть пустым")
        return None
    if len(value) > 30:
        raise ValueError(f"{label} должен содержать не более 30 символов")
    return value


def _parse_birthday(value: str | None) -> date | None:
    if not value:
        return None
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("birthday должен быть в формате YYYY-MM-DD") from exc
    return validate_birthday(parsed)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Добавить нового администратора в систему"
    )
    parser.add_argument("--username", help="логин администратора (только латиница)")
    parser.add_argument(
        "--password",
        help="пароль администратора; если не указан, будет запрошен интерактивно",
    )
    parser.add_argument("--first-name", dest="first_name", help="имя")
    parser.add_argument("--last-name", dest="last_name", help="фамилия")
    parser.add_argument("--patronymic", help="отчество (необязательно)")
    parser.add_argument("--birthday", help="дата рождения в формате YYYY-MM-DD")
    return parser


def main() -> int:
    args = _build_parser().parse_args()

    try:
        username = _validate_username(args.username or _prompt("Логин"))
        password = _validate_password(
            args.password if args.password is not None else _prompt_password()
        )
        first_name = _validate_name(
            "имя", args.first_name or _prompt("Имя"), required=True
        )
        last_name = _validate_name(
            "фамилия", args.last_name or _prompt("Фамилия"), required=True
        )
        patronymic = _validate_name("отчество", args.patronymic or "", required=False)
        birthday = _parse_birthday(args.birthday)
    except ValueError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 1

    db = SessionLocal()
    try:
        existing = db.execute(
            select(User).where(User.username == username)
        ).scalar_one_or_none()
        if existing is not None:
            print(f"Ошибка: пользователь {username!r} уже существует", file=sys.stderr)
            return 1

        admin = User(
            username=username,
            password_hash=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            patronymic=patronymic,
            birthday=birthday,
            role="admin",
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
    except IntegrityError:
        db.rollback()
        print(f"Ошибка: пользователь {username!r} уже существует", file=sys.stderr)
        return 1
    except SQLAlchemyError as exc:
        db.rollback()
        print(f"Ошибка базы данных: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()

    print(f"Администратор {username!r} создан (id: {admin.id})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
