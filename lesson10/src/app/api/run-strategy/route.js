import { NextResponse } from 'next/server';
import { runStrategySimulation } from '../../../lib/engine.mjs';

export async function POST(request) {
  try {
    const body = await request.json().catch(() => ({}));
    const result = await runStrategySimulation(body);
    return NextResponse.json(result);
  } catch (error) {
    return NextResponse.json({ error: error?.message || 'Failed to run strategy' }, { status: 500 });
  }
}

export async function GET() {
  const result = await runStrategySimulation({ symbol: 'BTC', riskProfile: 'balanced', goal: 'capture_trend' });
  return NextResponse.json(result);
}
