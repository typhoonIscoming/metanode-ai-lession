import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma/prisma.service';

@Injectable()
export class SalariesService {
  constructor(private readonly prisma: PrismaService) {}

  async snapshot() {
    const [byRole, bySeniority, byRemote, overall] = await Promise.all([
      this.prisma.$queryRawUnsafe<Array<any>>(`
        SELECT t.slug, t.name,
               COUNT(*)::int            as job_count,
               ROUND(AVG(j.salary_min))::int as avg_min,
               ROUND(AVG(j.salary_max))::int as avg_max,
               MIN(j.salary_min)::int   as min_min,
               MAX(j.salary_max)::int   as max_max
        FROM tags t
        JOIN job_tags jt ON jt.tag_id = t.id
        JOIN jobs j ON j.id = jt.job_id
        WHERE j.status = 'live'
          AND j.salary_min IS NOT NULL AND j.salary_max IS NOT NULL
          AND t.category IN ('skill','role')
        GROUP BY t.id
        HAVING COUNT(*) > 0
        ORDER BY avg_max DESC
        LIMIT 25
      `),
      this.prisma.$queryRawUnsafe<Array<any>>(`
        SELECT seniority::text          as seniority,
               COUNT(*)::int            as job_count,
               ROUND(AVG(j.salary_min))::int as avg_min,
               ROUND(AVG(j.salary_max))::int as avg_max
        FROM jobs j
        WHERE j.status = 'live'
          AND j.salary_min IS NOT NULL AND j.salary_max IS NOT NULL
          AND seniority IS NOT NULL
        GROUP BY seniority
        ORDER BY avg_max DESC
      `),
      this.prisma.$queryRawUnsafe<Array<any>>(`
        SELECT (CASE WHEN is_remote THEN 'remote' ELSE 'onsite' END) as kind,
               COUNT(*)::int as job_count,
               ROUND(AVG(salary_min))::int as avg_min,
               ROUND(AVG(salary_max))::int as avg_max
        FROM jobs WHERE status='live' AND salary_min IS NOT NULL AND salary_max IS NOT NULL
        GROUP BY kind
      `),
      this.prisma.$queryRawUnsafe<Array<any>>(`
        SELECT COUNT(*)::int as job_count,
               ROUND(AVG(salary_min))::int as avg_min,
               ROUND(AVG(salary_max))::int as avg_max,
               MIN(salary_min)::int as min_min,
               MAX(salary_max)::int as max_max
        FROM jobs WHERE status='live' AND salary_min IS NOT NULL AND salary_max IS NOT NULL
      `),
    ]);
    return {
      overall: overall[0] ?? null,
      byRole, bySeniority, byRemote,
      updatedAt: new Date().toISOString(),
    };
  }
}
