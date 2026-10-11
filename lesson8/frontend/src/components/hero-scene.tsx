'use client';
import { Canvas, useFrame } from '@react-three/fiber';
import { Float } from '@react-three/drei';
import { useMemo, useRef } from 'react';
import type { Group, Mesh } from 'three';

function FloatingCube({ position, scale }: { position: [number, number, number]; scale: number }) {
  const meshRef = useRef<Mesh>(null);
  useFrame((_, delta) => {
    if (!meshRef.current) return;
    meshRef.current.rotation.x += delta * 0.6;
    meshRef.current.rotation.y += delta * 0.4;
  });
  return (
    <Float speed={1.6} rotationIntensity={0.2} floatIntensity={0.8}>
      <mesh ref={meshRef} position={position} scale={scale}>
        <boxGeometry args={[0.6, 0.6, 0.6]} />
        <meshBasicMaterial color="#67e8f9" wireframe transparent opacity={0.55} />
      </mesh>
    </Float>
  );
}

function Icosa() {
  const ref = useRef<Mesh>(null);
  useFrame((_, delta) => {
    if (!ref.current) return;
    ref.current.rotation.y += delta * 0.18;
    ref.current.rotation.x += delta * 0.05;
  });
  return (
    <Float speed={1.2} rotationIntensity={0.4} floatIntensity={0.6}>
      <mesh ref={ref}>
        <icosahedronGeometry args={[1.4, 1]} />
        <meshBasicMaterial color="#c084fc" wireframe transparent opacity={0.85} />
      </mesh>
    </Float>
  );
}

function Scene() {
  const cubes = useMemo<Array<{ position: [number, number, number]; scale: number }>>(() => [
    { position: [-2.5,  1.6, -0.5], scale: 0.55 },
    { position: [ 2.4,  1.2,  0.4], scale: 0.40 },
    { position: [-1.8, -1.7,  0.6], scale: 0.50 },
    { position: [ 2.0, -1.3, -0.3], scale: 0.45 },
    { position: [ 0.0,  2.4,  0.8], scale: 0.30 },
    { position: [-2.8, -0.2,  0.5], scale: 0.35 },
    { position: [ 2.8,  0.1, -0.6], scale: 0.42 },
  ], []);

  const groupRef = useRef<Group>(null);
  useFrame((_, delta) => {
    if (!groupRef.current) return;
    groupRef.current.rotation.y += delta * 0.08;
  });

  return (
    <group ref={groupRef}>
      <Icosa />
      {cubes.map((c, i) => (
        <FloatingCube key={i} position={c.position} scale={c.scale} />
      ))}
    </group>
  );
}

export default function HeroScene() {
  if (typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    return null;
  }
  return (
    <div aria-hidden className="pointer-events-none absolute inset-y-0 right-0 hidden md:block w-1/2">
      <Canvas
        dpr={[1, 1.5]}
        gl={{ antialias: true, alpha: true }}
        camera={{ position: [0, 0, 5.5], fov: 50 }}
      >
        <Scene />
      </Canvas>
    </div>
  );
}
