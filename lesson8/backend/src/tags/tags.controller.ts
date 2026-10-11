import { Controller, Get, Param, Query } from '@nestjs/common';
import { TagsService } from './tags.service';
import { Public } from '../common/decorators/public.decorator';

@Public()
@Controller('tags')
export class TagsController {
  constructor(private readonly tags: TagsService) {}

  @Get()
  list(
    @Query('category') category?: string,
    @Query('popular') popular?: string,
    @Query('limit') limit?: string,
  ) {
    return this.tags.list({
      category,
      popular: popular === 'true' || popular === '1',
      limit: limit ? Number(limit) : undefined,
    });
  }

  @Get(':slug')
  bySlug(@Param('slug') slug: string) {
    return this.tags.bySlug(slug);
  }
}
