/**
 * DMN utilities.
 */

// Build a regex for variable name. Specification: https://www.omg.org/spec/DMN/1.3/PDF,
// section 10.3.1.2.

const nameStartChars = [
  // a-z (case insensitive) and literal `?` and `_` characters
  '?A-Za-z_',
  // unicode ranges
  '\\u00C0-\\u00D6',
  '\\u00D8-\\u00F6',
  '\\u00F8-\\u02FF',
  '\\u0370-\\u037D',
  '\\u037F-\\u1FFF',
  '\\u200C-\\u200D',
  '\\u2070-\\u218F',
  '\\u2C00-\\u2FEF',
  '\\u3001-\\uD7FF',
  '\\uF900-\\uFDCF',
  '\\uFDF0-\\uFFFD',
  // additional plane, the basic plane ranges only to U+FFFF
  '\\u{10000}-\\u{EFFFF}',
].join('');

const namePartChars = [
  nameStartChars,
  '0-9', // digits
  '\\u00B7',
  '\\u0300-\\u036F',
  '\\u203F-\\u2040',
  '.',
  '/',
  '-',
  '’',
  '+',
  '*',
].join('');

/**
 * Test for if an expression is possibly a variable name itself.
 *
 * See the DMN 1.3 spec, sections 10.3.1.2 and 10.3.1.4 for the full grammar and rules.
 *
 * The regex needs to be unicode aware to support multi-plane unicode ranges (that's the
 * \u{...} syntax above).
 */
export const namePattern = new RegExp(`^[${nameStartChars}][${namePartChars}]*$`, 'u');

export const detectMappingProblems = (intl, {formVariable, dmnVariable}) => {
  const problems = [];

  if (!formVariable && dmnVariable) {
    problems.push(
      intl.formatMessage({
        description: 'DMN in/output mapping: detected empty form variable',
        defaultMessage: 'No form variable specified (anymore).',
      })
    );
  }
  return problems;
};
