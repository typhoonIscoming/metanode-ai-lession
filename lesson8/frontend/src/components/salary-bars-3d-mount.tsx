'use client';
import dynamic from 'next/dynamic';

export const SalaryBars3D = dynamic(() => import('@/components/salary-bars-3d'), {
  ssr: false,
  loading: () => null,
});
