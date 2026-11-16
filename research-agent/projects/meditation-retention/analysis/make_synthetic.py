"""СИНТЕТИЧЕСКИЕ данные для демонстрации конвейера. НЕ реальные данные приложения.
Воспроизводимо: seed=42. Запуск: python projects/meditation-retention/analysis/make_synthetic.py
Модель: 1500 установок за октябрь 2026, наблюдение до 2026-11-14; цель онбординга
(sleep/stress/curiosity) и факт завершения первой сессии влияют на вероятность вернуться."""
import csv, random, datetime as dt
from pathlib import Path

random.seed(42)
out = Path(__file__).resolve().parent.parent / "materials" / "SYNTHETIC_events.csv"
start, end = dt.date(2026, 10, 1), dt.date(2026, 11, 14)
base = {"sleep": 0.55, "stress": 0.42, "curiosity": 0.30}
rows = []
for i in range(1500):
    goal = random.choices(list(base), weights=[0.35, 0.40, 0.25])[0]
    first_done = random.random() < (0.70 if goal == "sleep" else 0.55)
    inst = start + dt.timedelta(days=random.randrange(31))
    uid = f"u{i:05d}"
    rows.append((uid, inst, inst, goal, int(first_done)))
    churn0 = (0.45 if not first_done else 0.28) * (0.8 if goal == "sleep" else 1.0)
    q = base[goal] + 0.15                       # вероятность открыть приложение, пока «жив»
    day = 0
    while True:
        day += 1
        if inst + dt.timedelta(days=day) > end:
            break
        churn = churn0 if day <= 3 else 0.06     # основной отток в первые 3 дня, потом медленный
        if random.random() < churn:
            break
        if random.random() < q:
            rows.append((uid, inst, inst + dt.timedelta(days=day), goal, int(first_done)))
with out.open("w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["user_id", "install_date", "event_date", "goal", "first_session_done"])
    w.writerows(rows)
print(f"{out} — {len(rows)} строк")
