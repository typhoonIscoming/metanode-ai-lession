import { Controller, Get } from '@nestjs/common';
import { SalariesService } from './salaries.service';
import { Public } from '../common/decorators/public.decorator';

@Public()
@Controller('salaries')
export class SalariesController {
  constructor(private readonly svc: SalariesService) {}

  @Get()
  snapshot() { return this.svc.snapshot(); }
}
