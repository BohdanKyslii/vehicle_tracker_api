import logging

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from asgiref.sync import sync_to_async
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction

from apps.accounts.models import Profile
from apps.accounts.notifications import notify_admin_new_registration
from apps.cars.models import Car, Driver

logger = logging.getLogger(__name__)

router = Router(name="accounts")

CONTACT_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Надіслати номер телефону", request_contact=True)]],
    resize_keyboard=True,
    one_time_keyboard=True,
)


class DriverRegistration(StatesGroup):
    """Кроки після поділу контактом: ПІБ → посвідчення водія → створення заявки."""

    waiting_name = State()
    waiting_license = State()


class CarAssignment(StatesGroup):
    """Стан адміна/логіста одразу після підтвердження заявки водія ролью DRIVER."""

    waiting_plate_digits = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Вітаю! Це бот реєстрації водіїв Vehicle Cost Tracker.\n\n"
        "Щоб зареєструватись, поділіться, будь ласка, своїм номером телефону "
        "кнопкою нижче.",
        reply_markup=CONTACT_KEYBOARD,
    )


@sync_to_async
def _get_driver_profile(telegram_id: int) -> Profile | None:
    return Profile.objects.select_related("user").filter(telegram_id=telegram_id).first()


@sync_to_async
def _create_driver_registration(
    telegram_id: int, phone: str, name_driver: str, drivers_license: str
) -> Profile:
    """
    Створює User(is_active=False) + Driver + Profile(role=DRIVER) і одразу
    лінкує Profile.driver до нової картки водія — раніше цей зв'язок
    виставлявся вручну в Django Admin (бот знав лише телефон, не ПІБ/
    посвідчення, тому не міг сам створити Driver).
    """
    with transaction.atomic():
        user = User.objects.create_user(username=f"tg_{telegram_id}", is_active=False)
        user.set_unusable_password()
        user.save(update_fields=["password"])
        driver = Driver.objects.create(
            name_driver=name_driver,
            phone=phone,
            drivers_license=drivers_license,
        )
        profile = Profile.objects.create(
            user=user,
            role=Profile.Role.DRIVER,
            phone=phone,
            telegram_id=telegram_id,
            driver=driver,
        )
    return profile


@router.message(F.contact)
async def on_contact(message: Message, state: FSMContext) -> None:
    contact = message.contact
    if contact.user_id != message.from_user.id:
        await message.answer(
            "Будь ласка, надішліть саме СВІЙ контакт кнопкою нижче, "
            "а не переслану картку іншої людини.",
            reply_markup=CONTACT_KEYBOARD,
        )
        return

    existing = await _get_driver_profile(contact.user_id)
    if existing is not None:
        text = (
            "Ви вже зареєстровані та підтверджені. Відкрийте застосунок кнопкою меню."
            if existing.user.is_active
            else "Заявку вже надіслано, очікуйте підтвердження диспетчера."
        )
        await message.answer(text, reply_markup=ReplyKeyboardRemove())
        return

    await state.update_data(phone=contact.phone_number, telegram_id=contact.user_id)
    await state.set_state(DriverRegistration.waiting_name)
    await message.answer(
        "Дякуємо! Тепер вкажіть, будь ласка, ваше ПІБ повністю:",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(DriverRegistration.waiting_name)
async def on_driver_name(message: Message, state: FSMContext) -> None:
    name_driver = (message.text or "").strip()
    if not name_driver:
        await message.answer("ПІБ не може бути порожнім. Введіть ще раз:")
        return

    await state.update_data(name_driver=name_driver)
    await state.set_state(DriverRegistration.waiting_license)
    await message.answer("Тепер вкажіть номер посвідчення водія:")


@router.message(DriverRegistration.waiting_license)
async def on_driver_license(message: Message, state: FSMContext) -> None:
    drivers_license = (message.text or "").strip()
    if not drivers_license:
        await message.answer("Номер посвідчення не може бути порожнім. Введіть ще раз:")
        return

    data = await state.get_data()
    await state.clear()

    profile = await _create_driver_registration(
        telegram_id=data["telegram_id"],
        phone=data["phone"],
        name_driver=data["name_driver"],
        drivers_license=drivers_license,
    )
    await sync_to_async(notify_admin_new_registration)(profile.user)
    await message.answer(
        "Дякуємо! Заявку надіслано. Очікуйте підтвердження диспетчера — "
        "ми повідомимо, коли акаунт буде активовано."
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
async def on_approve(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback):
        await callback.answer("Немає прав", show_alert=True)
        return

    _, role, user_id_str = callback.data.split(":", 2)
    valid_roles = {value for value, _ in Profile.Role.choices}
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

    # Тільки для ролі DRIVER — одразу пропонуємо закріпити авто, не чекаючи
    # окремого походу в Django Admin.
    if role == Profile.Role.DRIVER and callback.message:
        await state.update_data(assign_car_user_id=user_id)
        await state.set_state(CarAssignment.waiting_plate_digits)
        await callback.message.answer(
            "Закріпити за водієм авто? Введіть 4 цифри держ. номера "
            "(наприклад 1234) або /skip, щоб пропустити."
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


@sync_to_async
def _find_cars_by_digits(digits: str) -> list[Car]:
    return list(Car.objects.filter(number_car__icontains=digits, is_active=True))


@sync_to_async
def _assign_car(user_id: int, car_id: int) -> str:
    """
    Прив'язує Car до Driver водія (user_id → Profile.driver). Якщо авто вже
    закріплене за ІНШИМ водієм (наприклад той на лікарняному, а це авто
    тимчасово передають підміні) — знімаємо зі старого, Driver.car це
    OneToOneField, одне авто = один водій одночасно.
    """
    try:
        user = User.objects.select_related("profile__driver").get(id=user_id)
    except User.DoesNotExist:
        return "Помилка: користувача не знайдено."

    driver = user.profile.driver
    if driver is None:
        return "Помилка: у водія ще немає картки Driver."

    try:
        car = Car.objects.select_related("driver").get(id=car_id)
    except Car.DoesNotExist:
        return "Помилка: авто не знайдено."

    note = ""
    old_driver = getattr(car, "driver", None)
    if old_driver is not None and old_driver.id != driver.id:
        old_driver.car = None
        old_driver.save(update_fields=["car"])
        note = f" Знято з водія «{old_driver.name_driver}»."

    driver.car = car
    driver.save(update_fields=["car"])
    return f"🚚 Призначено авто {car.number_car} ({car.name_car}).{note}"


def _car_choice_keyboard(cars: list[Car], user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{car.number_car} — {car.name_car}",
                    callback_data=f"assigncar:{car.id}:{user_id}",
                )
            ]
            for car in cars
        ]
    )


@router.message(CarAssignment.waiting_plate_digits, F.text == "/skip")
async def on_skip_car_assignment(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "Гаразд, авто не призначено. Зробити це можна пізніше в Django Admin "
        "(картка Driver → поле «Закріплене авто»)."
    )


@router.message(CarAssignment.waiting_plate_digits)
async def on_car_plate_digits(message: Message, state: FSMContext) -> None:
    digits = (message.text or "").strip()
    if not digits.isdigit() or len(digits) != 4:
        await message.answer("Введіть рівно 4 цифри держ. номера (або /skip):")
        return

    data = await state.get_data()
    user_id = data.get("assign_car_user_id")
    matches = await _find_cars_by_digits(digits)

    if not matches:
        await message.answer(f"Авто з цифрами «{digits}» не знайдено. Спробуйте ще раз (або /skip):")
        return

    if len(matches) > 1:
        await state.clear()
        await message.answer(
            "Знайдено кілька авто, оберіть потрібне:",
            reply_markup=_car_choice_keyboard(matches, user_id),
        )
        return

    await state.clear()
    result = await _assign_car(user_id, matches[0].id)
    await message.answer(result)


@router.callback_query(F.data.startswith("assigncar:"))
async def on_assign_car_choice(callback: CallbackQuery) -> None:
    if not _is_admin(callback):
        await callback.answer("Немає прав", show_alert=True)
        return

    _, car_id_str, user_id_str = callback.data.split(":", 2)
    result = await _assign_car(int(user_id_str), int(car_id_str))
    await callback.answer("Готово")
    if callback.message:
        await callback.message.edit_text(f"{callback.message.text}\n\n{result}")


def build_dispatcher() -> Dispatcher:
    # MemoryStorage — стан FSM живе в пам'яті процесу бота, губиться при
    # рестарті контейнера. Прийнятно для короткого діалогу (кілька повідомлень
    # поспіль), не потрібна БД-персистентність заради цього.
    dp = Dispatcher(storage=MemoryStorage())
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
