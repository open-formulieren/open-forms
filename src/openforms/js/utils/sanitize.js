import DOMPurify from 'dompurify';

const ALLOWED_HTML_TAGS = [
  // Basic text tags
  'a',
  'b',
  'br',
  'em',
  'h1',
  'h2',
  'h3',
  'h4',
  'h5',
  'h6',
  'i',
  'p',
  's',
  'strong',
  'sup',
  'u',
  // Lists
  'li',
  'ol',
  'ul',
];

const ALLOWED_HTML_ATTRIBUTES = ['href', 'target', 'rel'];

export const sanitizeHTML = data => {
  return DOMPurify.sanitize(data, {
    ALLOWED_TAGS: ALLOWED_HTML_TAGS,
    ALLOWED_ATTR: ALLOWED_HTML_ATTRIBUTES,
    ALLOW_DATA_ATTR: true,
  });
};
