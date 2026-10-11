import './globals.css';
import type { Metadata } from 'next';
import { SiteHeader } from '@/components/site-header';
import { SiteFooter } from '@/components/site-footer';
import { GridBackground } from '@/components/grid-background';
import { ShaderBg } from '@/components/shader-bg';

export const metadata: Metadata = {
  title: 'web3.career — On-chain Job Board',
  description: 'Discover blockchain, smart contract and crypto roles at the most-funded Web3 protocols.',
  metadataBase: new URL('http://localhost:3000'),
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <body className="min-h-screen antialiased scanline relative" suppressHydrationWarning>
        <ShaderBg />
        <GridBackground />
        <SiteHeader />
        <main>{children}</main>
        <SiteFooter />
      </body>
    </html>
  );
}
