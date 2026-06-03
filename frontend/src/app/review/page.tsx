import { QuizRunner } from "@/components/QuizRunner";

// The /api/quiz/next endpoint already prioritizes due (spaced-repetition)
// questions, so the review screen reuses the same runner with a larger batch.
export default function Review() {
  return <QuizRunner title="復習（間隔反復で再出題）" sessionSize={12} />;
}
