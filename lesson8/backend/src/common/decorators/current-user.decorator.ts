import { ExecutionContext, createParamDecorator } from '@nestjs/common';

export interface AuthUser {
  sub: string;
  role: 'candidate' | 'employer' | 'admin';
  email: string;
}

export const CurrentUser = createParamDecorator(
  (_data: unknown, ctx: ExecutionContext): AuthUser | undefined => {
    const req = ctx.switchToHttp().getRequest<{ user?: AuthUser }>();
    return req.user;
  },
);
