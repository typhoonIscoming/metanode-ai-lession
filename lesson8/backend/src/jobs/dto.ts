import { IsArray, IsBoolean, IsEmail, IsEnum, IsInt, IsOptional, IsString, IsUrl, Max, MaxLength, Min, MinLength } from 'class-validator';
import { Type } from 'class-transformer';

export class CreateJobDto {
  @IsString() @MinLength(3) @MaxLength(160)
  title!: string;

  @IsString() @MinLength(30)
  description!: string;

  @IsOptional() @IsString() @MaxLength(160)
  location?: string;

  @IsBoolean()
  isRemote!: boolean;

  @IsOptional() @IsEnum(['intern', 'junior', 'mid', 'senior', 'lead', 'exec'])
  seniority?: 'intern' | 'junior' | 'mid' | 'senior' | 'lead' | 'exec';

  @IsOptional() @IsEnum(['full_time', 'part_time', 'contract', 'internship'])
  employmentType?: 'full_time' | 'part_time' | 'contract' | 'internship';

  @IsOptional() @IsInt() @Min(0) @Max(1_000_000)
  salaryMin?: number;

  @IsOptional() @IsInt() @Min(0) @Max(1_000_000)
  salaryMax?: number;

  @IsEnum(['external', 'internal'])
  applyType!: 'external' | 'internal';

  @IsOptional() @IsUrl()
  applyUrl?: string;

  @IsOptional() @IsEmail()
  applicationEmail?: string;

  @IsArray() @IsString({ each: true })
  tags!: string[];
}

export class ListJobsDto {
  @IsOptional() @Type(() => Number) @IsInt() @Min(1)
  page?: number;

  @IsOptional() @Type(() => Number) @IsInt() @Min(1) @Max(100)
  limit?: number;

  @IsOptional() @IsString()
  q?: string;

  @IsOptional() @IsString()
  tag?: string;

  @IsOptional() @IsString()
  company?: string;

  @IsOptional() @Type(() => Boolean) @IsBoolean()
  remote?: boolean;

  @IsOptional() @Type(() => Number) @IsInt() @Min(0)
  salaryMin?: number;

  @IsOptional() @IsEnum(['recent', 'salary'])
  sort?: 'recent' | 'salary';
}
