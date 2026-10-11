import { Controller, Get, Param, Query } from '@nestjs/common';
import { CompaniesService } from './companies.service';
import { Public } from '../common/decorators/public.decorator';

@Public()
@Controller('companies')
export class CompaniesController {
  constructor(private readonly companies: CompaniesService) {}

  @Get()
  list(@Query('page') page?: string, @Query('limit') limit?: string, @Query('q') q?: string) {
    return this.companies.list({
      page: page ? Number(page) : undefined,
      limit: limit ? Number(limit) : undefined,
      q,
    });
  }

  @Get(':slug')
  bySlug(@Param('slug') slug: string) {
    return this.companies.bySlug(slug);
  }
}
