import { Body, Controller, Post } from '@nestjs/common';
import { IsEmail, IsOptional, IsString, MaxLength } from 'class-validator';
import { SubscribeService } from './subscribe.service';
import { Public } from '../common/decorators/public.decorator';

class SubscribeDto {
  @IsEmail() email!: string;
  @IsOptional() @IsString() @MaxLength(80) firstName?: string;
  @IsOptional() @IsString() @MaxLength(80) lastName?: string;
  @IsOptional() @IsString() @MaxLength(40) source?: string;
}

@Public()
@Controller('subscribe')
export class SubscribeController {
  constructor(private readonly svc: SubscribeService) {}

  @Post()
  subscribe(@Body() dto: SubscribeDto) {
    return this.svc.subscribe(dto.email, dto.firstName, dto.lastName, dto.source);
  }
}
