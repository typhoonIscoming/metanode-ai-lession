import { redirect } from "next/navigation";

// 根路径直接跳转到仪表盘（PRD §3.1）
export default function RootPage() {
  redirect("/dashboard");
}
