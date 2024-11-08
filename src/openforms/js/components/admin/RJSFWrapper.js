import {isSelect} from '@rjsf/core/lib/utils';
import PropTypes from 'prop-types';

import {FAIcon} from './icons';

/*
 Adapted from:
 https://github.com/rjsf-team/react-jsonschema-form/blob/master/packages/core/src/components/fields/SchemaField.js#L128
 */
const CustomFieldTemplate = ({
  id,
  label,
  children,
  errors,
  rawErrors,
  rawDescription,
  hidden,
  required,
  displayLabel,
  schema,
}) => {
  const isNullBoolean = isSelect(schema) && schema.type.includes('boolean');
  if (hidden) {
    return <div className="hidden">{children}</div>;
  }

  // label should be displayed for nullable boolean dropdowns
  const hideLabel = !displayLabel && !isNullBoolean;

  return (
    <div className="rjsf-field">
      <div className={`rjsf-field__field ${rawErrors ? 'rjsf-field__field--error' : ''}`}>
        {!hideLabel && label && (
          <label className={`rjsf-field__label ${required ? 'required' : ''}`} htmlFor={id}>
            {label}
          </label>
        )}
        <div className="rjsf-field__input">{children}</div>
        {rawDescription && (
          <div className="rjsf-field__help">
            <FAIcon icon="question-circle" title={rawDescription} />
          </div>
        )}
      </div>
      {rawErrors && <div className="rjsf-field__errors">{errors}</div>}
    </div>
  );
};

CustomFieldTemplate.propTypes = {
  id: PropTypes.string,
  label: PropTypes.string,
  children: PropTypes.node.isRequired,
  errors: PropTypes.element,
  rawErrors: PropTypes.arrayOf(PropTypes.string),
  rawDescription: PropTypes.oneOfType([PropTypes.string, PropTypes.element]),
  hidden: PropTypes.bool,
  required: PropTypes.bool,
  displayLabel: PropTypes.bool,
  /*
  Schema prop is deliberately ignored as it doesn't seem to do anything.
  This will be revisited when/if we upgrade to a newer version.
  Relevant discussion: https://github.com/open-formulieren/open-forms/pull/3740#discussion_r1475756728
  */
  schema: PropTypes.object.isRequired,
};

export {CustomFieldTemplate};
