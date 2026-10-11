import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "@/components/ui/sonner";
import { QueryProvider } from "@/components/query-provider";
import { Navbar } from "@/components/navbar";
import { FooterDisclaimer } from "@/components/footer-disclaimer";

export const metadata: Metadata = {
  title: "BTC 套利信号 · Polymarket Arb Terminal",
  description: "Polymarket BTC 二元市场量化 + LLM 套利信号交易终端",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" className="h-full antialiased" suppressHydrationWarning>
      <body className="flex min-h-full flex-col text-slate-100">
        <QueryProvider>
          <Navbar />
          <div className="flex-1">{children}</div>
          <FooterDisclaimer />
        </QueryProvider>
        <Toaster richColors theme="dark" position="bottom-right" />
      </body>
    </html>
  );
}
