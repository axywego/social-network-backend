# Backend

## Для запуска на сервере

- важно рядом с докеркомпозом init.sql файлик в котором будет ```CREATE EXTENSION IF NOT EXISTS pg_trgm;``` чтобы работали норм индексы в бд
- докерфайл понятно зачем
- создать в директории app пути static/avatars static/posts static/private_storage/chat_images
че еще хммм не помню еще дополню

- python -m app.scripts.add_admin --username admin --first-name name --last-name surname
