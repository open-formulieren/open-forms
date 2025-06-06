import PropTypes from 'prop-types';
import {useContext} from 'react';

import {
  ValidationErrorContext,
  ValidationErrorsProvider,
  filterErrors,
} from 'components/admin/forms/ValidationErrors';
import {getReactSelectOptionsFromSchema} from 'utils/json-schema';

import LoAOverride from '../LoAOverride';

const DigidOptionsFormFields = ({name, plugin}) => {
  const validationErrors = useContext(ValidationErrorContext);
  const relevantErrors = filterErrors(name, validationErrors);

  const loaOptions = getReactSelectOptionsFromSchema(
    plugin.schema.properties.loa.enum,
    plugin.schema.properties.loa.enumNames,
    '------'
  );

  return (
    <ValidationErrorsProvider errors={relevantErrors}>
      <LoAOverride name="loa" options={loaOptions} />
    </ValidationErrorsProvider>
  );
};

DigidOptionsFormFields.propType = {
  name: PropTypes.string.isRequired,
  plugin: PropTypes.shape({
    id: PropTypes.string.isRequired,
    label: PropTypes.string.isRequired,
    providesAuth: PropTypes.oneOf(['bsn']).isRequired,
    schema: PropTypes.exact({
      type: PropTypes.oneOf(['object']).isRequired,
      properties: PropTypes.shape({
        loa: PropTypes.exact({
          type: PropTypes.oneOf(['string']).isRequired,
          title: PropTypes.string.isRequired,
          description: PropTypes.string.isRequired,
          enum: PropTypes.arrayOf(PropTypes.string).isRequired,
          enumNames: PropTypes.arrayOf(PropTypes.string).isRequired,
        }).isRequired,
      }),
    }).isRequired,
  }).isRequired,
};

export default DigidOptionsFormFields;
