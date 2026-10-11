import { Module } from '@nestjs/common';
import { SalariesService } from './salaries.service';
import { SalariesController } from './salaries.controller';

@Module({ providers: [SalariesService], controllers: [SalariesController] })
export class SalariesModule {}
