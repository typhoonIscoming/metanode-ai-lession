import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class CompaniesService {
  constructor(private readonly prisma: PrismaService) {}

  async list(params: { page?: number; limit?: number; q?: string }) {
    const page = Math.max(params.page ?? 1, 1);
    const limit = Math.min(params.limit ?? 25, 100);
    const skip = (page - 1) * limit;

    const where = params.q ? { name: { contains: params.q, mode: 'insensitive' as const } } : {};

    const [items, total] = await Promise.all([
      this.prisma.company.findMany({
        where,
        skip,
        take: limit,
        orderBy: [{ isVerified: 'desc' }, { name: 'asc' }],
        include: {
          _count: { select: { jobs: { where: { status: 'live' } } } },
        },
      }),
      this.prisma.company.count({ where }),
    ]);

    return {
      data: items.map(({ _count, fundingTotalUsd, ...rest }) => ({
        ...rest,
        fundingTotalUsd: fundingTotalUsd ? Number(fundingTotalUsd) : null,
        openRolesCount: _count.jobs,
      })),
      meta: { pagination: { page, limit, total, totalPages: Math.ceil(total / limit) } },
    };
  }

  async bySlug(slug: string) {
    const company = await this.prisma.company.findUnique({
      where: { slug },
      include: {
        jobs: {
          where: { status: 'live' },
          orderBy: { postedAt: 'desc' },
          take: 20,
          include: { tags: { include: { tag: true } } },
        },
      },
    });
    if (!company) throw new NotFoundException('Company not found');
    const { fundingTotalUsd, jobs, ...rest } = company;
    return {
      ...rest,
      fundingTotalUsd: fundingTotalUsd ? Number(fundingTotalUsd) : null,
      jobs: jobs.map((j) => ({ ...j, tags: j.tags.map((jt) => jt.tag) })),
    };
  }
}
