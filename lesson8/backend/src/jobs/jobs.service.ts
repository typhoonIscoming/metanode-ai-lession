import { ForbiddenException, Injectable, NotFoundException } from '@nestjs/common';
import { Prisma } from '@prisma/client';
import { PrismaService } from '../prisma/prisma.service';
import { CreateJobDto, ListJobsDto } from './dto';
import { randomBytes } from 'crypto';

@Injectable()
export class JobsService {
  constructor(private readonly prisma: PrismaService) {}

  async list(query: ListJobsDto) {
    const page = query.page ?? 1;
    const limit = query.limit ?? 25;
    const skip = (page - 1) * limit;

    const where: Prisma.JobWhereInput = { status: 'live' };
    if (query.q) where.OR = [
      { title: { contains: query.q, mode: 'insensitive' } },
      { description: { contains: query.q, mode: 'insensitive' } },
    ];
    if (query.remote !== undefined) where.isRemote = query.remote;
    if (query.salaryMin !== undefined) where.salaryMax = { gte: query.salaryMin };
    if (query.company) where.company = { slug: query.company };
    if (query.tag) where.tags = { some: { tag: { slug: query.tag } } };

    const orderBy: Prisma.JobOrderByWithRelationInput =
      query.sort === 'salary' ? { salaryMax: 'desc' } : { postedAt: 'desc' };

    const [items, total] = await Promise.all([
      this.prisma.job.findMany({
        where, orderBy, skip, take: limit,
        include: {
          company: { select: { id: true, slug: true, name: true, logoUrl: true } },
          tags: { include: { tag: true }, orderBy: { position: 'asc' } },
        },
      }),
      this.prisma.job.count({ where }),
    ]);

    return {
      data: items.map((j) => this.serialize(j)),
      meta: { pagination: { page, limit, total, totalPages: Math.ceil(total / limit) } },
    };
  }

  async bySlug(slug: string) {
    const job = await this.prisma.job.findUnique({
      where: { slug },
      include: {
        company: true,
        tags: { include: { tag: true }, orderBy: { position: 'asc' } },
      },
    });
    if (!job || job.status !== 'live') throw new NotFoundException('Job not found');
    await this.prisma.job.update({ where: { id: job.id }, data: { viewsCount: { increment: 1 } } });
    return this.serialize(job);
  }

  async create(userId: string, role: 'candidate' | 'employer' | 'admin', dto: CreateJobDto) {
    if (role !== 'employer' && role !== 'admin') throw new ForbiddenException('Only employers can post jobs');

    const company = await this.prisma.company.findFirst({ where: { ownerUserId: userId } });
    if (!company) throw new ForbiddenException('No company profile linked to this account');

    const tags = await this.prisma.tag.findMany({ where: { slug: { in: dto.tags } } });
    if (tags.length === 0) throw new ForbiddenException('At least one valid tag required');

    const slug = makeSlug(dto.title);
    const created = await this.prisma.job.create({
      data: {
        slug,
        title: dto.title,
        description: dto.description,
        location: dto.location,
        isRemote: dto.isRemote,
        seniority: dto.seniority,
        employmentType: dto.employmentType ?? 'full_time',
        salaryMin: dto.salaryMin,
        salaryMax: dto.salaryMax,
        applyType: dto.applyType,
        applyUrl: dto.applyUrl,
        applicationEmail: dto.applicationEmail,
        companyId: company.id,
        postedByUserId: userId,
        status: 'live',
        expiresAt: new Date(Date.now() + 60 * 24 * 3600 * 1000),
        tags: { create: tags.map((t, idx) => ({ tagId: t.id, position: idx })) },
      },
      include: {
        company: true,
        tags: { include: { tag: true } },
      },
    });
    return this.serialize(created);
  }

  private serialize(j: any) {
    return {
      id: j.id,
      slug: j.slug,
      title: j.title,
      description: j.description,
      location: j.location,
      isRemote: j.isRemote,
      seniority: j.seniority,
      employmentType: j.employmentType,
      salaryMin: j.salaryMin,
      salaryMax: j.salaryMax,
      salaryCurrency: j.salaryCurrency,
      applyType: j.applyType,
      applyUrl: j.applyUrl,
      applicationEmail: j.applicationEmail,
      postedAt: j.postedAt,
      expiresAt: j.expiresAt,
      viewsCount: j.viewsCount,
      company: j.company ? {
        id: j.company.id,
        slug: j.company.slug,
        name: j.company.name,
        logoUrl: j.company.logoUrl,
      } : null,
      tags: j.tags?.map((jt: any) => ({ slug: jt.tag.slug, name: jt.tag.name, category: jt.tag.category })) ?? [],
    };
  }
}

function makeSlug(title: string): string {
  const base = title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '').slice(0, 80);
  return `${base || 'job'}-${randomBytes(3).toString('hex')}`;
}
