# Vehicle Cost Tracker — Project Memory

Ця директорія (`vehicle_tracker_api`) містить проект **Vehicle Cost Tracker**.
Уся документація та контекст проекту зберігаються в `task_description/`.

## Стан проекту (читається автоматично щосесії)

@task_description/STATE.md

## Порядок читання документації

1. `task_description/transport/01_PROJECT_OVERVIEW.md` — бізнес-логіка та ролі
2. `task_description/AGENTS_GLOBAL.md` — архітектура, стек, правила (обов'язково перед роботою)
3. `task_description/STATE.md` — поточний стан (вже підвантажено вище)
4. `task_description/TASK.md` — конкретне поточне завдання
5. `task_description/AI_AGENT_CONTEXT.md` — технічні деталі (типи, mock-дані, бізнес-логіка)

## Правило оновлення пам'яті

Після будь-якої значної зміни в проекті — онови `task_description/STATE.md`
(розділ "Що зроблено", "Наступні кроки", дату оновлення) і за потреби
додай запис у `task_description/CHANGES.md`. Це єдине джерело пам'яті
про стан проекту між сесіями.
