import logging
from typing import Callable
from uuid import UUID

from telegram import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, InvalidCallbackData

from band_tracker.bot.helpers.callback_data import get_callback_data
from band_tracker.bot.helpers.context import BTContext
from band_tracker.bot.helpers.interfaces import MessageManager
from band_tracker.core.artist import Artist
from band_tracker.core.enums import MessageType
from band_tracker.db.errors import ArtistNotFound, UserNotFound

log = logging.getLogger(__name__)


def _unfollowed_markup(artist_id: UUID) -> InlineKeyboardMarkup:
    row1 = [
        InlineKeyboardButton("Follow", callback_data=f"follow {artist_id}"),
    ]
    row2 = [
        InlineKeyboardButton("Events", callback_data=f"eventsar {artist_id} 0"),
        InlineKeyboardButton("Buy Tickets", callback_data=f"tickets {artist_id}"),
    ]
    markup = InlineKeyboardMarkup([row1, row2])
    return markup


def _followed_markup(artist_id: UUID) -> InlineKeyboardMarkup:
    row1 = [
        InlineKeyboardButton("Unfollow", callback_data=f"unfollow {artist_id}"),
        InlineKeyboardButton(
            "Configure notifications", callback_data=f"notifications {artist_id}"
        ),
    ]
    row2 = [
        InlineKeyboardButton("Events", callback_data=f"eventsar {artist_id} 0"),
        InlineKeyboardButton("Buy Tickets", callback_data=f"tickets {artist_id}"),
    ]
    markup = InlineKeyboardMarkup([row1, row2])
    return markup


def _amp_text(artist: Artist) -> str:
    text_data = f"<b>{artist.name}</b>\n\n"
    if artist.genres:
        genres = " ".join(artist.genres)
        genres_str = f"Genres: {genres}\n"
        text_data += genres_str
    if artist.socials.instagram:
        text_data += f'<a href="{artist.socials.instagram}">Instagram</a>\n'
    if artist.socials.youtube:
        text_data += f'<a href="{artist.socials.youtube}">YouTube</a>\n'
    if artist.socials.spotify:
        text_data += f'<a href="{artist.socials.spotify}">Spotify</a>\n'
    return text_data


def _get_callback_artist_id(query: CallbackQuery | None) -> UUID:
    result_text = get_callback_data(query=query)
    try:
        artist_id = UUID(result_text)
    except ValueError:
        raise InvalidCallbackData("Invalid artist id")
    return artist_id


async def _change_markup(
    update: Update,
    ctx: BTContext,
    markup_generator: Callable[[UUID], InlineKeyboardMarkup],
    artist_id: UUID,
) -> None:
    query = update.callback_query

    assert query
    assert query.message

    await query.answer()
    new_markup = markup_generator(artist_id)
    await ctx.bot.edit_message_reply_markup(  # pyright: ignore
        chat_id=query.message.chat_id,
        message_id=query.message.message_id,
        reply_markup=new_markup,
    )


async def follow(update: Update, ctx: BTContext) -> None:
    query = update.callback_query
    try:
        artist_id = _get_callback_artist_id(query)
    except InvalidCallbackData as e:
        log.warning(e.message)
        return

    assert update.effective_user
    user = await ctx.user()

    try:
        await ctx.dal.add_follow(user_tg_id=user.tg_id, artist_id=artist_id)
    except ArtistNotFound:
        log.warning("Can't create a follow, artist is not present in db")
        return
    except UserNotFound:
        log.warning("Can't create a follow, user is not present in db")
        return

    await _change_markup(
        update=update,
        ctx=ctx,
        markup_generator=_followed_markup,
        artist_id=artist_id,
    )


async def unfollow(update: Update, ctx: BTContext) -> None:
    query = update.callback_query
    try:
        artist_id = _get_callback_artist_id(query)
    except InvalidCallbackData as e:
        log.warning(e.message)
        return

    assert update.effective_user
    user = await ctx.user()
    await ctx.dal.unfollow(user_tg_id=user.tg_id, artist_id=artist_id)
    await _change_markup(
        update=update,
        ctx=ctx,
        markup_generator=_unfollowed_markup,
        artist_id=artist_id,
    )


async def artist_button(update: Update, ctx: BTContext) -> None:
    query = update.callback_query
    assert query
    await query.answer()

    try:
        artist_id = _get_callback_artist_id(query)
    except InvalidCallbackData as e:
        log.warning(e.message)
        return

    artist = await ctx.dal.get_artist(artist_id)
    await _show_artist(ctx=ctx, artist=artist)


async def artist_command(_: Update, ctx: BTContext) -> None:
    user = await ctx.user()
    args = ctx.args
    if not args:
        await ctx.msg.send_text(
            msg_type=MessageType.ARTIST_ERROR,
            user=user,
            markup=None,
            text="Please enter an artist name",
        )
        return

    name = " ".join(args)

    if len(name) > 255:
        name = name[:255]

    artist = await ctx.dal.get_artist_by_name(name)
    await _show_artist(ctx=ctx, artist=artist)


async def _show_artist(ctx: BTContext, artist: Artist | None) -> None:
    user = await ctx.user()
    msg: MessageManager = ctx.bot_data["msg"]

    if artist is None:
        await ctx.msg.send_text(
            markup=None,
            text="Can't find an artist",
            user=user,
            msg_type=MessageType.ARTIST_ERROR,
        )
        return

    if artist.id in user.follows:
        markup = _followed_markup(artist.id)
    else:
        markup = _unfollowed_markup(artist.id)
    if artist.image is None:
        log.warning(f"Artist {artist.id} does not have an image")
        return
    await msg.send_image(
        text=_amp_text(artist),
        markup=markup,
        user=user,
        image=artist.image,
        msg_type=MessageType.AMP,
    )


handlers = [
    CommandHandler("artist", artist_command),
    CallbackQueryHandler(callback=artist_button, pattern="artist .*"),
    CallbackQueryHandler(callback=follow, pattern="follow .*"),
    CallbackQueryHandler(callback=unfollow, pattern="unfollow .*"),
]
