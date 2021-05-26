const CURRENT_URL = new URL(window.location);

/**
 * Build a fully qualified URL (protocol, netloc) for a given path.
 *
 * Use this to build absolute URLs to same-host API endpoints, used to circumvent
 * Formio prefixing the URL with the FormIO base URL, for example.
 * @param  {String} path The path to build a URL for, including leading slash.
 * @return {String}      The fully qualified URL, taken from the current host.
 */
export const getFullyQualifiedUrl = (url) => {
    const fq = `${CURRENT_URL.protocol}//${CURRENT_URL.host}${url}`;
    return fq;
};
