# TASK.md — Поточне завдання

> Перед заповненням прочитай `AGENTS_GLOBAL.md` та `AI_AGENT_CONTEXT.md`.
> Очищуй цей файл і пиши нове завдання перед кожною задачею.

---

## Metadata

| Поле       | Значення                                                          |
|------------|--------------------------------------------------------------------|
| Проект     | Vehicle Cost Tracker                                              |
| Тип        | Bug / Enhancement / New Feature / Refactor                        |
| Пріоритет  | Low / Medium / High / Critical                                    |
| Статус     | Todo / In Progress / Review / Done                                |
| App(s)     | accounts / cars / products / customers / waybills / logistics / analytics |
| Складність | S / M / L / XL                                                    |

---

## Мета

<!-- Одне речення: що треба зробити і навіщо -->

---

## Опис

<!-- Детальний опис завдання:
- Що зараз є (поточна поведінка)
- Що повинно бути (очікувана поведінка)
- Які моделі/serializers/views зачеплені
-->

---

## Скриншоти / Мокапи

<!-- Посилання на файли в images/ або вставити опис UI -->

---

## Технічні вимоги

### Backend (Django + DRF)
- [ ] `viewsets.ModelViewSet` + `DefaultRouter`, не function-based views
- [ ] `get_permissions()` за роллю (класи з `apps/accounts/permissions.py`)
- [ ] `ModelSerializer` з явним `fields`/`read_only_fields`
- [ ] `on_delete=PROTECT` або `SET_NULL` (не `CASCADE` без потреби)
- [ ] `DecimalField` для фінансових даних
- [ ] `verbose_name`/`help_text` українською на нових полях моделі

### Frontend (окремий репозиторій `vehicle_cost_tracker`)
- [ ] Функціональний компонент (FC) з типізованими пропсами
- [ ] Дані через хук на TanStack Query (`src/hocks/`)
- [ ] Tailwind CSS, без окремих CSS-файлів
- [ ] Мобільна адаптація (мін. 44px touch targets)

### URLs
- [ ] `DefaultRouter` у `apps/<app>/urls.py`
- [ ] Підключити в `config/urls.py`, якщо новий застосунок

### Міграції
- [ ] `python manage.py makemigrations` після зміни моделей
- [ ] `python manage.py migrate`

---

## Критерії прийняття (Acceptance Criteria)

- [ ] ...
- [ ] ...
- [ ] `ruff check .` — 0 помилок
- [ ] `python manage.py check` — чисто

---

## Definition of Done

- [ ] Всі acceptance criteria виконані
- [ ] `ruff check .` та `ruff format .` — чисто
- [ ] Міграції створені та застосовані
- [ ] Немає регресій в інших модулях
- [ ] Коміт зі стислим змістовним описом "чому" (проєкт не дотримується
      суворо Conventional Commits — див. `AGENTS_GLOBAL.md` §7)
