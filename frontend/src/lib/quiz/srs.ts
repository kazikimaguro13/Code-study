// TS port of backend/src/store/progress.py ProgressStore._schedule — SM-2-lite SRS.

export interface SrsState {
  q_id: string;
  attempts: number;
  correct_streak: number;
  ease: number;
  interval_days: number;
  due_date: string; // ISO-8601 date (YYYY-MM-DD)
  last_score: number;
  last_seen: string | null;
}

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

function addDays(dateStr: string, days: number): string {
  const d = new Date(dateStr + "T00:00:00");
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

export function schedule(current: SrsState | null, score: number, correct: boolean): SrsState {
  const attempts = (current?.attempts ?? 0) + 1;
  let ease = current?.ease ?? 2.5;
  let streak = current?.correct_streak ?? 0;
  let interval = current?.interval_days ?? 0;

  if (correct) {
    streak += 1;
    if (streak === 1) {
      interval = 1;
    } else if (streak === 2) {
      interval = 3;
    } else {
      interval = Math.min(365, Math.max(1, Math.round(interval * ease)));
    }
    ease = Math.min(2.7, ease + 0.1);
  } else {
    streak = 0;
    interval = 0;
    ease = Math.max(1.3, ease - 0.2);
  }

  const today = todayIso();
  return {
    q_id: current?.q_id ?? "",
    attempts,
    correct_streak: streak,
    ease: Math.round(ease * 1000) / 1000,
    interval_days: interval,
    due_date: addDays(today, interval),
    last_score: score,
    last_seen: new Date().toISOString(),
  };
}
