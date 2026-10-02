"use client";
import ApiErrorView from "@/components/ApiErrorView";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <ApiErrorView error={error} reset={reset} />;
}
