'use client';
import { useEffect, useRef } from 'react';

interface TiltProps {
  max?: number;
  className?: string;
  children: React.ReactNode;
}

// pure helper, suitable for unit tests
export function computeTilt(
  rect: { left: number; top: number; width: number; height: number },
  clientX: number,
  clientY: number,
  max: number,
): { rotateX: number; rotateY: number; px: number; py: number } {
  const nx = (clientX - rect.left) / rect.width - 0.5;
  const ny = (clientY - rect.top) / rect.height - 0.5;
  return {
    rotateX: -ny * 2 * max,
    rotateY: nx * 2 * max,
    px: ((nx + 0.5) * 100),
    py: ((ny + 0.5) * 100),
  };
}

export function Tilt({ max = 8, className, children }: TiltProps) {
  const ref = useRef<HTMLDivElement>(null);
  const sheenRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    if (!window.matchMedia('(hover: hover) and (pointer: fine)').matches) return;

    const el = ref.current;
    const sheen = sheenRef.current;
    if (!el) return;

    let raf = 0;
    let next: { x: number; y: number } | null = null;

    function apply() {
      if (!next || !el) { raf = 0; return; }
      const rect = el.getBoundingClientRect();
      const { rotateX, rotateY, px, py } = computeTilt(rect, next.x, next.y, max);
      el.style.transform =
        `perspective(1000px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg)`;
      if (sheen) {
        sheen.style.background =
          `radial-gradient(circle at ${px}% ${py}%, rgba(255,255,255,0.10), transparent 55%)`;
        sheen.style.opacity = '1';
      }
      next = null;
      raf = 0;
    }

    function onMove(e: PointerEvent) {
      next = { x: e.clientX, y: e.clientY };
      if (!raf) raf = requestAnimationFrame(apply);
    }
    function onLeave() {
      if (raf) cancelAnimationFrame(raf);
      raf = 0;
      next = null;
      el!.style.transform = '';
      if (sheen) sheen.style.opacity = '0';
    }

    el.addEventListener('pointermove', onMove);
    el.addEventListener('pointerleave', onLeave);
    return () => {
      el.removeEventListener('pointermove', onMove);
      el.removeEventListener('pointerleave', onLeave);
      if (raf) cancelAnimationFrame(raf);
    };
  }, [max]);

  return (
    <div
      ref={ref}
      className={(className ?? '') + ' relative will-change-transform transition-transform duration-300 ease-out'}
      style={{ transformStyle: 'preserve-3d' }}
    >
      {children}
      <div
        ref={sheenRef}
        aria-hidden
        className="pointer-events-none absolute inset-0 rounded-[inherit] opacity-0 transition-opacity duration-300"
      />
    </div>
  );
}
