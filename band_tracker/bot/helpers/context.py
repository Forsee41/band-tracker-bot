import logging

from telegram import Bot, Chat, Message, Update
from telegram import User as TGUser
from telegram.ext import Application, CallbackContext

from band_tracker.bot.helpers.get_user import get_user
from band_tracker.bot.helpers.interfaces import MessageManager
from band_tracker.core.user import User
from band_tracker.db.dal_bot import BotDAL

log = logging.getLogger(__name__)


class BTContext(CallbackContext[Bot, dict, dict, dict]):
    _update: Update
    _user: User | None = None
    _tg_user: TGUser | None = None
    _chat: Chat | None = None
    _message: Message | None = None

    dal: BotDAL
    msg: MessageManager

    @property
    def tg_user(self) -> TGUser:
        if not self._tg_user:
            tg_user = self._update.effective_user
            if not tg_user:
                msg = "Can't find an effective user of an update"
                log.warning(msg)
                raise ValueError(msg)
            self._tg_user = tg_user
        return self._tg_user

    @property
    def chat(self) -> Chat:
        if not self._chat:
            chat = self._update.effective_chat
            if not chat:
                msg = "Can't find an effective chat of an update"
                log.warning(msg)
                raise ValueError(msg)
            self._chat = chat
        return self._chat

    @property
    def message(self) -> Message:
        if not self._message:
            message = self._update.effective_message
            if not message:
                msg = "Can't find an effective message of an update"
                log.warning(msg)
                raise ValueError(msg)
            self._message = message
        return self._message

    async def user(self) -> User:
        if self._user is None:
            user = await get_user(tg_user=self.tg_user, dal=self.dal)
            self._user = user
        return self._user

    @classmethod
    def from_update(cls: type, update: object, application: Application) -> "BTContext":
        # mypy typechecking bug with factory classmethods
        context = super().from_update(  # type: ignore
            update=update, application=application
        )

        assert isinstance(update, Update)
        context._update = update
        context.dal = context.bot_data["dal"]
        context.msg = context.bot_data["msg"]

        return context
