import { Injectable, NotFoundException } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class ArticlesService {
  constructor(private readonly prisma: PrismaService) {}

  async list(params: { category?: string; limit?: number; page?: number }) {
    const page = Math.max(params.page ?? 1, 1);
    const limit = Math.min(params.limit ?? 50, 100);
    const skip = (page - 1) * limit;
    const where = params.category ? { category: params.category as any } : {};
    const [items, total] = await Promise.all([
      this.prisma.article.findMany({ where, skip, take: limit, orderBy: { publishedAt: 'desc' } }),
      this.prisma.article.count({ where }),
    ]);
    return { data: items, meta: { pagination: { page, limit, total, totalPages: Math.ceil(total / limit) } } };
  }

  async bySlug(slug: string) {
    const article = await this.prisma.article.findUnique({ where: { slug } });
    if (!article) throw new NotFoundException('Article not found');
    return article;
  }

  async categories() {
    const counts = await this.prisma.article.groupBy({
      by: ['category'],
      _count: { category: true },
    });
    return counts.map((c) => ({ category: c.category, count: c._count.category }));
  }
}
