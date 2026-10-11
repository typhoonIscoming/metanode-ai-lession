'use client';
import { useEffect, useState } from 'react';

export function StatCounter({ value, label, suffix }: { value: number; label: string; suffix?: string }) {
  const [n, setN] = useState(0);
  useEffect(() => {
    const start = performance.now();
    const dur = 1400;
    let raf = 0;
    const tick = (t: number) => {
      const p = Math.min((t - start) / dur, 1);
      setN(Math.floor(p * value));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [value]);
  return (
    <div>
      <div className="font-mono text-3xl md:text-4xl font-semibold tracking-tight text-zinc-50">
        {new Intl.NumberFormat('en-US').format(n)}{suffix ?? ''}
      </div>
      <div className="mt-1 text-xs uppercase tracking-widest text-zinc-500">{label}</div>
    </div>
  );
}
