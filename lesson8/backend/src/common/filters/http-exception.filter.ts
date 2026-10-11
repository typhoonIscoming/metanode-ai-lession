import { ArgumentsHost, Catch, ExceptionFilter, HttpException, HttpStatus, Logger } from '@nestjs/common';
import { Request, Response } from 'express';
import { randomUUID } from 'crypto';

interface ErrorBody {
  error: {
    code: string;
    message: string;
    request_id: string;
    fields?: Record<string, string>;
  };
}

@Catch()
export class AllExceptionsFilter implements ExceptionFilter {
  private readonly logger = new Logger(AllExceptionsFilter.name);

  catch(exception: unknown, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const res = ctx.getResponse<Response>();
    const req = ctx.getRequest<Request>();
    const requestId = (req.headers['x-request-id'] as string) ?? randomUUID();

    let status = HttpStatus.INTERNAL_SERVER_ERROR;
    let code = 'SERVER_ERROR';
    let message = 'Internal server error';
    let fields: Record<string, string> | undefined;

    if (exception instanceof HttpException) {
      status = exception.getStatus();
      const r = exception.getResponse();
      if (typeof r === 'string') {
        message = r;
      } else if (typeof r === 'object' && r !== null) {
        const obj = r as { message?: string | string[]; error?: string };
        if (Array.isArray(obj.message)) {
          message = obj.message.join('; ');
          fields = Object.fromEntries(obj.message.map((m) => [m, m]));
        } else if (typeof obj.message === 'string') {
          message = obj.message;
        }
      }
      code = httpStatusToCode(status);
    } else if (exception instanceof Error) {
      this.logger.error(exception.message, exception.stack);
    }

    const body: ErrorBody = { error: { code, message, request_id: requestId, ...(fields ? { fields } : {}) } };
    res.status(status).json(body);
  }
}

function httpStatusToCode(status: number): string {
  switch (status) {
    case 400: return 'BAD_REQUEST';
    case 401: return 'AUTH_REQUIRED';
    case 403: return 'FORBIDDEN';
    case 404: return 'NOT_FOUND';
    case 409: return 'CONFLICT';
    case 422: return 'VALIDATION_FAILED';
    case 429: return 'RATE_LIMITED';
    default:  return status >= 500 ? 'SERVER_ERROR' : 'ERROR';
  }
}
