# CLAUDE.md — Швидкий довідник для AI Агентів (v3)

Контекст проекту для AI-агентів. Перед роботою обов'язково читай `AGENTS_GLOBAL.md`.

---

## Проект

**Vehicle Cost Tracker** — React PWA додаток для обліку транспортних витрат.

**Технічний стек:**
- React 18, TypeScript, Vite
- Tailwind CSS
- TanStack Query v5 (Data fetching/caching)
- Lucide React (Icons)
- Recharts (Data visualization)

---

## Команди (Project Root)

```bash
npm install         # Встановити залежності
npm run dev         # Запуск dev-сервера
npm run build       # Збірка проекту
npm run lint        # Перевірка ESLint
```

---

## Стиль коду та правила

- **Компоненти:** Тільки функціональні компоненти (FC).
- **Типи:** Обов'язкова типізація пропсів та стейту. Суворий TypeScript.
- **Стилі:** Тільки Tailwind CSS. Уникати CSS-файлів.
- **Дані:** Робота з даними тільки через хуки TanStack Query.
- **Бізнес-логіка:** Розрахунки та форматування виносити в `utils/`.

---

## Патерни коду

### 1. Функціональний компонент
```tsx
import React from 'react';
import { Badge } from '../ui/Badge';

interface Props {
  status: 'active' | 'repair';
}

export const CarStatus: React.FC<Props> = ({ status }) => {
  return (
    <div className="flex items-center gap-2">
      <Badge variant={status === 'active' ? 'success' : 'warning'}>
        {status}
      </Badge>
    </div>
  );
};
```

### 2. Використання TanStack Query
```tsx
const { data, isLoading } = useQuery({
  queryKey: ['cars'],
  queryFn: fetchCars
});
```

### 3. Tailwind для мобільних
```tsx
<button className="min-h-[44px] w-full bg-blue-600 text-white rounded-lg active:bg-blue-700">
  Підтвердити
</button>
```

---

## Алгоритм роботи

1. Перевірити `STATE.md` — на якому етапі проект.
2. Прочитати `TASK.md` — що треба зробити.
3. Ознайомитись з `transport/` документацією якщо завдання складне.
4. Оновити `STATE.md` після завершення роботи.
