"""Аутентификация — пропускаем сообщения только от одного Telegram аккаунта"""
from aiogram import types
from aiogram import BaseMiddleware
from typing import Dict, Any, Awaitable, Callable


class AccessMiddleware(BaseMiddleware):
    def __init__(self, access_id: list):
        self.access_id = [int(i) for i in access_id]
        super().__init__()

    async def __call__(
            self,
            handler: Callable[[types.Message, Dict[str, Any]], Awaitable[Any]],
            event: types.Message,
            data: Dict[str, Any]
    ) -> Any:
        if event.from_user.id not in self.access_id:
            return await event.answer(f"Отказано в доступе")
        return await handler(event, data)
