import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class UsersService {
  constructor(private readonly prisma: PrismaService) {}

  async getMe(userId: string) {
    const user = await this.prisma.user.findUnique({
      where: { id: userId },
      include: {
        ownedCompanies: { select: { id: true, slug: true, name: true, logoUrl: true } },
      },
    });
    if (!user) throw new NotFoundException('User not found');
    return {
      id: user.id,
      email: user.email,
      role: user.role,
      displayName: user.displayName,
      emailVerifiedAt: user.emailVerifiedAt,
      companies: user.ownedCompanies,
      createdAt: user.createdAt,
    };
  }
}
