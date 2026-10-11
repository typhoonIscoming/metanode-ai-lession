'use client';
import { Canvas, useFrame } from '@react-three/fiber';
import { Billboard, Text } from '@react-three/drei';
import { useMemo, useRef } from 'react';
import type { Group } from 'three';

interface Row {
  slug: string;
  name: string;
  avg_max: number;
}

function lerpHex(a: string, b: string, t: number): string {
  const pa = parseInt(a.slice(1), 16);
  const pb = parseInt(b.slice(1), 16);
  const ar = (pa >> 16) & 0xff, ag = (pa >> 8) & 0xff, ab = pa & 0xff;
  const br = (pb >> 16) & 0xff, bg = (pb >> 8) & 0xff, bb = pb & 0xff;
  const r = Math.round(ar + (br - ar) * t);
  const g = Math.round(ag + (bg - ag) * t);
  const bl = Math.round(ab + (bb - ab) * t);
  return '#' + [(r << 16) | (g << 8) | bl].map((v) => v.toString(16).padStart(6, '0'))[0];
}

function Bars({ rows }: { rows: Row[] }) {
  const groupRef = useRef<Group>(null);
  useFrame((_, delta) => {
    if (!groupRef.current) return;
    groupRef.current.rotation.y += delta * 0.06;
  });

  const maxVal = useMemo(() => rows.reduce((m, r) => Math.max(m, r.avg_max), 1), [rows]);
  const count = rows.length;
  const spacing = 1.2;
  const offset = -((count - 1) * spacing) / 2;

  return (
    <group ref={groupRef}>
      {rows.map((r, i) => {
        const t = r.avg_max / maxVal;
        const height = Math.max(0.2, t * 3.6);
        const color = lerpHex('#22d3ee', '#c084fc', t);
        return (
          <group key={r.slug} position={[offset + i * spacing, 0, 0]}>
            {/* solid bar */}
            <mesh position={[0, height / 2, 0]}>
              <boxGeometry args={[0.6, height, 0.6]} />
              <meshBasicMaterial color={color} transparent opacity={0.92} />
            </mesh>

            {/* salary label — billboarded so it always faces the camera */}
            <Billboard position={[0, height + 0.42, 0]}>
              <Text
                fontSize={0.26}
                color="#f3f4f6"
                anchorX="center"
                anchorY="middle"
                outlineWidth={0.012}
                outlineColor="#05070d"
              >
                {`$${Math.round(r.avg_max / 1000)}k`}
              </Text>
            </Billboard>

            {/* role label below the floor — also billboarded */}
            <Billboard position={[0, -0.55, 0]}>
              <Text
                fontSize={0.18}
                color="#a3a3a3"
                anchorX="center"
                anchorY="middle"
                maxWidth={1.1}
                textAlign="center"
                outlineWidth={0.008}
                outlineColor="#05070d"
              >
                {r.name}
              </Text>
            </Billboard>
          </group>
        );
      })}

      {/* subtle floor grid — sunken slightly so it doesn't slice through bar bottoms */}
      <gridHelper
        args={[count * spacing + 3, count + 3, '#1e293b', '#0b1220']}
        position={[0, -0.02, 0]}
      />
    </group>
  );
}

export default function SalaryBars3D({ rows }: { rows: Row[] }) {
  if (typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    return null;
  }
  if (rows.length === 0) return null;
  const top10 = rows.slice(0, 10);
  return (
    <div aria-hidden className="glass rounded-xl overflow-hidden h-[480px]">
      <Canvas
        dpr={[1, 1.5]}
        gl={{ antialias: true, alpha: true }}
        camera={{ position: [0, 4.5, 13], fov: 38 }}
      >
        <Bars rows={top10} />
      </Canvas>
    </div>
  );
}
