# [Назва Завдання]

## Metadata

- **Project**: Vehicle Cost Tracker
- **Type**: [Баг / Покращення / Новий функціонал]
- **Priority**: [Low / Medium / High / Critical]
- **Status**: Pending
- **Estimated Complexity**: [Low / Medium / High]

---

## 1. Опис Завдання

### 🎯 Мета

[Короткий опис того, що потрібно зробити та навіщо]

### 📝 Детальний опис

[Розгорнутий опис проблеми або функціоналу]

### 📸 Скріншоти / Макети

[Посилання на скріншоти в директорії images/]

- ![Опис зображення](images/...)

### ✅ Критерії приймання

- [ ] Критерій 1
- [ ] Критерій 2
- [ ] Критерій 3

---

## 2. Технічні Вимоги та Рекомендації

### Backend (Django + DRF)

- **Views:** `viewsets.ModelViewSet` + `DefaultRouter`, не function-based views
- **Права доступу:** `get_permissions()` за роллю через класи з
  `apps/accounts/permissions.py` (`IsAuthenticated`, `IsManagerOrHead`,
  `IsManagerOrHeadOnly`, `IsLogistOrAbove`, `IsHeadOnly`)
- **Serializers:** `ModelSerializer` з явним `fields`
- **Models:** `on_delete=models.PROTECT` або `SET_NULL` для Foreign Keys,
  явний `db_table`, `verbose_name`/`help_text` українською

### Frontend (окремий репозиторій `vehicle_cost_tracker`)

- **UI:** Tailwind CSS, функціональні компоненти з TypeScript
- **Дані:** TanStack Query (`src/hocks/`), не прямі `fetch` у компонентах
- **Responsive:** мобільна адаптація, мін. 44px touch targets

### Дотримуйся правил з `AGENTS_GLOBAL.md`:

- ViewSet/serializer патерни
- Ексклюзивність каналів доставки (`own`/`hired`/`carrier`)
- Code style (Ruff)

---

## 3. Тестування та Валідація

- [ ] Перевірити права доступу за роллю (401/403 без авторизації —
      див. примітку в `AGENTS_GLOBAL.md` про `403` замість `401`)
- [ ] Перевірити роботу серіалізатора (валідація полів)
- [ ] `python manage.py check` — чисто

---

## 4. ✅ Definition of Done

Таска вважається виконаною коли:

- [ ] Всі критерії приймання виконані
- [ ] Код проходить `ruff check` та `ruff format`
- [ ] Міграції створені й накочені (якщо змінювались моделі)
- [ ] Немає регресій в існуючому функціоналі
