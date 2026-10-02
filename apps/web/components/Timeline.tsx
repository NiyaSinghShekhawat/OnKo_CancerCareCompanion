import { Fragment } from "react";
import type { CareEvent } from "@/lib/types";
import { fmtDate, fmtTime, statusText } from "@/lib/format";

export default function Timeline({ events }: { events: CareEvent[] }) {
  const chapters = new Set(events.map(e => e.journey_chapter ?? 1));
  const showChapters = chapters.size > 1;

  return (
    <ol className="ml-2 grid gap-5 border-l-2 border-onko-line pl-7">
      {events.map((e, index) => {
        const chapter = e.journey_chapter ?? 1;
        const previousChapter = index > 0 ? (events[index - 1].journey_chapter ?? 1) : null;
        const chapterStart = showChapters && previousChapter !== chapter;

        return (
          <Fragment key={e.id}>
            {chapterStart && (
              <li className="relative -ml-3">
                <span className="absolute -left-[24px] top-1/2 h-2.5 w-2.5 -translate-y-1/2 rounded-full bg-onko-teal" />
                <div className="inline-flex rounded-full border border-onko-line bg-white px-4 py-2 text-[12px] font-bold uppercase tracking-[.1em] text-onko-teal shadow-sm">
                  Chapter {chapter}
                </div>
              </li>
            )}
            <li className="relative rounded-xl bg-onko-surface p-5">
              <span className="absolute -left-[35px] top-6 h-3.5 w-3.5 rounded-full border-2 border-white bg-onko-teal ring-2 ring-onko-softteal" />
              <div className="text-[13px] font-semibold uppercase tracking-wide text-onko-muted">
                {fmtDate(e.scheduled_at)} · {fmtTime(e.scheduled_at)} · {e.type.toLowerCase()}
              </div>
              <div className="mt-1.5 text-[17px] font-bold">{e.title}</div>
              <div className="mt-1 text-[14px] font-medium text-onko-teal">{statusText[e.status]}</div>
              {e.details?.instructions && (
                <div className="mt-2 text-[14px] leading-6 text-onko-muted">{e.details.instructions}</div>
              )}
            </li>
          </Fragment>
        );
      })}
    </ol>
  );
}
