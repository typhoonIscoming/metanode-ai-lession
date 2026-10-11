"use client";

import { useSchedulerJobs } from "@/hooks/use-scheduler";
import { formatRelativeFromNow } from "@/lib/time";
import { cn } from "@/lib/utils";

// 顶栏右侧调度状态指示灯：绿/黄/红
// - 绿：API 正常 + 所有 job 有 next_run_at
// - 黄：API 正常但某个 job 没有 next_run_at（被关闭或卡住）
// - 红：API 不可达（query error）
export function SchedulerHealthIndicator() {
  const { data, isError, isPending } = useSchedulerJobs();

  let tone: "green" | "yellow" | "red" | "loading" = "loading";
  let tooltip = "正在检查调度状态…";

  if (isError) {
    tone = "red";
    tooltip = "无法连接后端调度服务";
  } else if (!isPending && data) {
    const missing = data.items.find((j) => !j.next_run_at);
    if (missing) {
      tone = "yellow";
      tooltip = `任务 ${missing.name} 没有下次执行时间`;
    } else {
      tone = "green";
      const daily = data.items.find((j) => j.name === "daily_discovery");
      const next = daily?.next_run_at
        ? `下次 daily_discovery: ${formatRelativeFromNow(daily.next_run_at)}`
        : "所有调度任务正常";
      tooltip = next;
    }
  }

  const dotClass = cn(
    "inline-block h-2.5 w-2.5 rounded-full",
    tone === "green" && "bg-emerald-500",
    tone === "yellow" && "bg-amber-500",
    tone === "red" && "bg-rose-500",
    tone === "loading" && "bg-slate-300",
  );

  return (
    <span
      className="inline-flex items-center gap-2 text-xs text-slate-500"
      title={tooltip}
      aria-label={tooltip}
    >
      <span className={dotClass} aria-hidden />
      <span className="hidden sm:inline">调度</span>
    </span>
  );
}
