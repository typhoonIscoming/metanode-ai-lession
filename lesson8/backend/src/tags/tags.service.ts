import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class TagsService {
  constructor(private readonly prisma: PrismaService) {}

  async list(params: { category?: string; popular?: boolean; limit?: number }) {
    const limit = Math.min(params.limit ?? 200, 500);

    if (params.popular) {
      const rows = await this.prisma.$queryRawUnsafe<Array<{ id: string; slug: string; name: string; category: string; count: bigint }>>(
        `SELECT t.id, t.slug, t.name, t.category::text AS category, COUNT(jt.tag_id)::bigint AS count
         FROM tags t
         LEFT JOIN job_tags jt ON jt.tag_id = t.id
         LEFT JOIN jobs j ON j.id = jt.job_id AND j.status = 'live'
         ${params.category ? "WHERE t.category::text = $1" : ''}
         GROUP BY t.id
         ORDER BY count DESC, t.name ASC
         LIMIT ${limit}`,
        ...(params.category ? [params.category] : []),
      );
      return rows.map((r) => ({ ...r, count: Number(r.count) }));
    }

    return this.prisma.tag.findMany({
      where: params.category ? { category: params.category as any } : undefined,
      orderBy: { name: 'asc' },
      take: limit,
    });
  }

  async bySlug(slug: string) {
    return this.prisma.tag.findUnique({ where: { slug } });
  }
}
