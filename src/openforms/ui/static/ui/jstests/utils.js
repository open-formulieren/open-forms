/**
 * Returns Promise which resolves in "timeout" milliseconds (1000 equals 1 second).
 * @param {number} [timeout=0] The timeout in milliseconds after which the Promise should resolve.
 * A value of 0 (default) causes the Promise to resolve at the end of the event loop.
 * @return {Promise}
 */
export const delay = (timeout=0) => {
  return new Promise(resolve => {
      setTimeout(resolve, timeout);
  });
};
