// See https://stackoverflow.com/a/43595110 and https://stackoverflow.com/a/32749533
class ExtendableError extends Error {
  constructor(message) {
    super(message);
    this.name = this.constructor.name;
    if (typeof Error.captureStackTrace === 'function') {
      Error.captureStackTrace(this, this.constructor);
    } else {
      this.stack = new Error(message).stack;
    }
  }
}

function FormException(message, details) {
  this.message = message;
  this.details = details;
}

class APIError extends ExtendableError {
  constructor(message, statusCode) {
    super(message);
    this.statusCode = statusCode;
  }
}

class ValidationErrors extends ExtendableError {
  constructor(message, errors) {
    super(message);
    this.errors = errors;
    this.context = null; // context for upstream error handlers
  }
}

class NotAuthenticatedError extends ExtendableError {}

export {ExtendableError};
export {FormException};
export {APIError, ValidationErrors, NotAuthenticatedError};
