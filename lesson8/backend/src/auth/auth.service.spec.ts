import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ConflictException, UnauthorizedException } from '@nestjs/common';
import { AuthService } from './auth.service';

function makePrisma() {
  return {
    user: {
      findUnique: vi.fn(),
      create: vi.fn(),
    },
    refreshToken: {
      create: vi.fn(),
      findUnique: vi.fn(),
      update: vi.fn(),
    },
    company: { create: vi.fn() },
    $transaction: vi.fn(async (fn: any) => fn(prismaShape)),
  } as any;
}

let prismaShape: any;

function makeJwt() {
  return {
    signAsync: vi.fn(async (payload: any, opts: any) => `signed:${payload.sub}:${opts?.secret ?? 'default'}`),
    verifyAsync: vi.fn(async (token: string) => {
      const [, sub] = token.split(':');
      return { sub, email: 'e', role: 'candidate' };
    }),
  } as any;
}

function makeConfig() {
  return {
    get: (k: string) => {
      const env: Record<string, any> = {
        JWT_SECRET: 'a'.repeat(32),
        JWT_REFRESH_SECRET: 'b'.repeat(32),
        JWT_ACCESS_TTL: 900,
        JWT_REFRESH_TTL: 2592000,
      };
      return env[k];
    },
  } as any;
}

describe('AuthService', () => {
  let prisma: ReturnType<typeof makePrisma>;
  let jwt: ReturnType<typeof makeJwt>;
  let service: AuthService;

  beforeEach(() => {
    prisma = makePrisma();
    prismaShape = prisma;
    jwt = makeJwt();
    service = new AuthService(prisma, jwt, makeConfig());
  });

  it('registers a new candidate and returns tokens', async () => {
    prisma.user.findUnique.mockResolvedValueOnce(null);
    prisma.user.create.mockResolvedValueOnce({ id: 'u1', email: 'a@b.com', role: 'candidate', displayName: null });

    const result = await service.register({ email: 'a@b.com', password: 'password1', role: 'candidate' });

    expect(result.user.email).toBe('a@b.com');
    expect(result.accessToken).toMatch(/^signed:u1:/);
    expect(result.refreshToken).toMatch(/^signed:u1:/);
    expect(prisma.user.create).toHaveBeenCalledOnce();
  });

  it('throws on duplicate email', async () => {
    prisma.user.findUnique.mockResolvedValueOnce({ id: 'x', email: 'a@b.com' });
    await expect(service.register({ email: 'a@b.com', password: 'password1', role: 'candidate' }))
      .rejects.toBeInstanceOf(ConflictException);
  });

  it('login returns tokens when password matches', async () => {
    const { hashSync } = await import('bcryptjs');
    prisma.user.findUnique.mockResolvedValueOnce({
      id: 'u1', email: 'a@b.com', role: 'candidate', passwordHash: hashSync('password1', 4), displayName: null,
    });
    const result = await service.login({ email: 'a@b.com', password: 'password1' });
    expect(result.accessToken).toMatch(/^signed:u1:/);
  });

  it('login rejects wrong password', async () => {
    const { hashSync } = await import('bcryptjs');
    prisma.user.findUnique.mockResolvedValueOnce({
      id: 'u1', email: 'a@b.com', role: 'candidate', passwordHash: hashSync('password1', 4), displayName: null,
    });
    await expect(service.login({ email: 'a@b.com', password: 'wrong' }))
      .rejects.toBeInstanceOf(UnauthorizedException);
  });
});
