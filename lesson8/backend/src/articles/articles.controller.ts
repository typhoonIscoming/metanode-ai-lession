import { Controller, Get, Param, Query } from '@nestjs/common';
import { ArticlesService } from './articles.service';
import { Public } from '../common/decorators/public.decorator';

@Public()
@Controller('articles')
export class ArticlesController {
  constructor(private readonly svc: ArticlesService) {}

  @Get()
  list(@Query('category') category?: string, @Query('page') page?: string, @Query('limit') limit?: string) {
    return this.svc.list({
      category,
      page: page ? Number(page) : undefined,
      limit: limit ? Number(limit) : undefined,
    });
  }

  @Get('categories')
  categories() {
    return this.svc.categories();
  }

  @Get(':slug')
  bySlug(@Param('slug') slug: string) {
    return this.svc.bySlug(slug);
  }
}
