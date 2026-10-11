import './globals.css';

export const metadata = {
  title: 'AI Strategy Cockpit',
  description: 'Hackathon demo for an AI-powered strategy cockpit',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body>{children}</body>
    </html>
  );
}
