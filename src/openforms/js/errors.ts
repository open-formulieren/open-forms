/**
 * Custom error/exception class definitions.
 *
 * @note This module should look similar to its counterpart in the SDK (``src/errors.ts``).
 */

// See https://stackoverflow.com/a/43595110 and https://stackoverflow.com/a/32749533
class ExtendableError extends Error {
  public constructor(message: string) {
    super(message);
    this.name = this.constructor.name;
    // Works in the browser, but NodeJS types trip over this when extracting library
    // types with vite-plugin-dts
    if ('captureStackTrace' in Error && typeof Error.captureStackTrace === 'function') {
      Error.captureStackTrace(this, this.constructor);
    } else {
      this.stack = new Error(message).stack;
    }
  }
}

export class APIError extends ExtendableError {
  public statusCode: number;
  public detail: string;
  public code: string;

  public constructor(message: string, statusCode: number, detail: string = '', code: string = '') {
    super(message);
    this.statusCode = statusCode;
    this.detail = detail;
    this.code = code;
  }
}

export interface InvalidParam {
  name: string;
  code: string;
  reason: string;
}

export interface Http400ResponseBody {
  type?: string;
  code: string;
  title: string;
  status: 400;
  detail: string;
  instance: string;
  invalidParams: InvalidParam[];
}

export class ValidationError extends ExtendableError {
  private _errors: InvalidParam[];

  public constructor(message: string, reponseBody: Http400ResponseBody | null) {
    super(message);
    this._errors = reponseBody?.invalidParams ?? [];
  }

  public get errors(): InvalidParam[] {
    return this._errors;
  }
}

export class NotAuthenticated extends APIError {}
export class PermissionDenied extends APIError {}
export class NotFound extends APIError {}
export class UnprocessableEntity extends APIError {}
export class ServiceUnavailable extends APIError {}
