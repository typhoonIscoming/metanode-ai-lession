import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class SubscribeService {
  constructor(private readonly prisma: PrismaService) {}

  async subscribe(email: string, firstName?: string, lastName?: string, source?: string) {
    const existing = await this.prisma.subscription.findUnique({ where: { email: email.toLowerCase() } });
    if (existing) {
      return { ok: true, alreadySubscribed: true };
    }
    await this.prisma.subscription.create({
      data: { email: email.toLowerCase(), firstName, lastName, source, status: 'active' },
    });
    return { ok: true, alreadySubscribed: false };
  }
}
