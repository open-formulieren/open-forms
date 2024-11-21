function isAsync(fn) {
  return fn && fn.constructor.name === 'AsyncFunction';
}

export {isAsync};
