# TASK.md — Поточне завдання

> Перед заповненням прочитай `AGENTS_GLOBAL.md` та `AI_AGENT_CONTEXT.md`.
> Очищуй цей файл і пиши нове завдання перед кожною задачею.

---

## Metadata

| Поле           | Значення                                      |
|----------------|-----------------------------------------------|
| Проект         | Expenses                                      |
| Тип            | Bug / Enhancement / New Feature / Refactor    |
| Пріоритет      | Low / Medium / High / Critical                |
| Статус         | Todo / In Progress / Review / Done            |
| App(s)         | transport / warehouse / shipment / accounts   |
| Складність     | S / M / L / XL                                |

---

## Мета

<!-- Одне речення: що треба зробити і навіщо -->

---

## Опис

<!-- Детальний опис завдання:
- Що зараз є (поточна поведінка)
- Що повинно бути (очікувана поведінка)
- Які файли/моделі/views зачеплені
-->

---

## Скриншоти / Мокапи

<!-- Посилання на файли в images/ або вставити опис UI -->

---

## Технічні вимоги

### Backend
- [ ] CBV (ListView / CreateView / UpdateView / DeleteView / TemplateView)
- [ ] ModelForm з django-crispy-forms + bootstrap5
- [ ] Валідація в `clean()` / `clean_<field>()`
- [ ] `on_delete=PROTECT` або `SET_NULL` (не CASCADE!)
- [ ] `DecimalField` для фінансових даних
- [ ] Docstrings для всіх нових функцій і класів

### Frontend
- [ ] Bootstrap 5 стилізація
- [ ] Django messages (success/error)
- [ ] Адаптивна верстка
- [ ] Фільтри через django-filter (якщо список)

### URLs
- [ ] Namespace: `app_name:action_name`
- [ ] Зареєструвати в головному `expenses/urls.py` (якщо новий app)

### Міграції
- [ ] `python manage.py makemigrations` після зміни моделей
- [ ] `python manage.py migrate`

---

## Критерії прийняття (Acceptance Criteria)

- [ ] ...
- [ ] ...
- [ ] `ruff check .` — 0 помилок
- [ ] Pre-commit hooks проходять
- [ ] Функціонал протестовано вручну

---

## Definition of Done

- [ ] Всі acceptance criteria виконані
- [ ] `ruff check .` та `ruff format .` — чисто
- [ ] Міграції створені та застосовані
- [ ] Немає регресій в інших модулях
- [ ] Коміт за Conventional Commits: `feat(app): description`
