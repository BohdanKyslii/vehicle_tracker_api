import logging

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.auth.models import User

from apps.accounts.models import Profile
from apps.accounts.notifications import notify_admin_new_registration

logger = logging.getLogger(__name__)

router = Router(name="accounts")

CONTACT_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Надіслати номер телефону", request_contact=True)]],
    resize_keyboard=True,
    one_time_keyboard=True,
)


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Вітаю! Це бот реєстрації водіїв Vehicle Cost Tracker.\n\n"
        "Щоб зареєструватись, поділіться, будь ласка, своїм номером телефону "
        "кнопкою нижче.",
        reply_markup=CONTACT_KEYBOARD,
    )


@sync_to_async
def _get_or_create_driver_profile(telegram_id: int, phone: str) -> tuple[Profile, bool]:
    profile = (
        Profile.objects.select_related("user").filter(telegram_id=telegram_id).first()
    )
    if profile is not None:
        return profile, False

    user = User.objects.create_user(username=f"tg_{telegram_id}", is_active=False)
    user.set_unusable_password()
    user.save(update_fields=["password"])
    profile = Profile.objects.create(
        user=user,
        role=Profile.Role.DRIVER,
        phone=phone,
        telegram_id=telegram_id,
    )
    return profile, True


@router.message(F.contact)
async def on_contact(message: Message) -> None:
    contact = message.contact
    if contact.user_id != message.from_user.id:
        await message.answer(
            "Будь ласка, надішліть саме СВІЙ контакт кнопкою нижче, "
            "а не переслану картку іншої людини.",
            reply_markup=CONTACT_KEYBOARD,
        )
        return

    profile, created = await _get_or_create_driver_profile(
        telegram_id=contact.user_id,
        phone=contact.phone_number,
    )

    if not created:
        text = (
            "Ви вже зареєстровані та підтверджені. Відкрийте застосунок кнопкою меню."
            if profile.user.is_active
            else "Заявку вже надіслано, очікуйте підтвердження диспетчера."
        )
        await message.answer(text, reply_markup=ReplyKeyboardRemove())
        return

    await sync_to_async(notify_admin_new_registration)(profile.user)
    await message.answer(
        "Дякуємо! Заявку надіслано. Очікуйте підтвердження диспетчера — "
        "ми повідомимо, коли акаунт буде активовано.",
        reply_markup=ReplyKeyboardRemove(),
    )


@sync_to_async
def _approve_user(user_id: int, role: str) -> int | None:
    """Активує акаунт із заданою роллю, повертає Profile.telegram_id (щоб сповістити)."""
    try:
        user = User.objects.select_related("profile").get(id=user_id)
    except User.DoesNotExist:
        return None
    user.is_active = True
    user.save(update_fields=["is_active"])
    user.profile.role = role
    user.profile.save(update_fields=["role"])
    return user.profile.telegram_id


@sync_to_async
def _reject_user(user_id: int) -> None:
    # is_active=False у фільтрі — захист від подвійного натискання: вже
    # підтвердженого користувача випадковим "Відхилити" не видалимо.
    User.objects.filter(id=user_id, is_active=False).delete()


def _is_admin(callback: CallbackQuery) -> bool:
    return callback.from_user.id in settings.TELEGRAM_ADMIN_IDS


@router.callback_query(F.data.startswith("approve:"))
async def on_approve(callback: CallbackQuery) -> None:
    if not _is_admin(callback):
        await callback.answer("Немає прав", show_alert=True)
        return

    _, role, user_id_str = callback.data.split(":", 2)
    valid_roles = {
        value for value, _ in Profile.Role.choices if value != Profile.Role.HEAD
    }
    if role not in valid_roles:
        await callback.answer("Невірна роль", show_alert=True)
        return

    user_id = int(user_id_str)
    role_label = dict(Profile.Role.choices)[role]
    driver_telegram_id = await _approve_user(user_id, role)
    await callback.answer(f"Підтверджено як {role_label}")
    if callback.message:
        await callback.message.edit_text(
            f"{callback.message.text}\n\n✅ Підтверджено як {role_label}"
        )
    if driver_telegram_id:
        await callback.bot.send_message(
            driver_telegram_id,
            "Вас підтверджено! Відкрийте застосунок кнопкою меню бота.",
        )


@router.callback_query(F.data.startswith("reject:"))
async def on_reject(callback: CallbackQuery) -> None:
    if not _is_admin(callback):
        await callback.answer("Немає прав", show_alert=True)
        return

    user_id = int(callback.data.split(":", 1)[1])
    await _reject_user(user_id)
    await callback.answer("Відхилено")
    if callback.message:
        await callback.message.edit_text(f"{callback.message.text}\n\n❌ Відхилено")


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(router)
    return dp


async def run() -> None:
    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = build_dispatcher()
    try:
        # Long polling вимагає відсутності вебхука — прибираємо старий про всяк випадок.
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
