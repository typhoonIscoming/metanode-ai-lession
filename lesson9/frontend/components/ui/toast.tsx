// PRD §2 列出 `toast.tsx`，shadcn/ui 新版用 sonner 替代旧 toast 实现
// 这里做透传，保持 PRD 文件清单一致；调用方既可用 `@/components/ui/toast` 也可用 sonner
export { Toaster } from "@/components/ui/sonner";
export { toast } from "sonner";
