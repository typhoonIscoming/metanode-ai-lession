'use client';
import dynamic from 'next/dynamic';

export const HeroScene = dynamic(() => import('@/components/hero-scene'), {
  ssr: false,
  loading: () => null,
});
