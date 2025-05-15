import PropTypes from 'prop-types';
import {useContext} from 'react';

import Fieldset from 'components/admin/forms/Fieldset';
import {
  ValidationErrorContext,
  ValidationErrorsProvider,
  filterErrors,
} from 'components/admin/forms/ValidationErrors';

import AdditionalScopesField from './AdditionalScopesField';
import AuthenticationAttributeField from './AuthenticationAttributeField';
import YiviOptionsFormBsnFields from './YiviOptionsFormBsnFields';

const YiviOptionsFormFields = ({name, plugin}) => {
  const validationErrors = useContext(ValidationErrorContext);
  const relevantErrors = filterErrors(name, validationErrors);

  return (
    <ValidationErrorsProvider errors={relevantErrors}>
      <Fieldset>
        <AuthenticationAttributeField schema={plugin.schema} />
        <AdditionalScopesField schema={plugin.schema} />

        <YiviOptionsFormBsnFields plugin={plugin} />
      </Fieldset>
    </ValidationErrorsProvider>
  );
};

YiviOptionsFormFields.propType = {
  name: PropTypes.string.isRequired,
  plugin: PropTypes.shape({
    id: PropTypes.string,
    label: PropTypes.string,
    providesAuth: PropTypes.string,
    schema: PropTypes.exact({
      type: PropTypes.oneOf(['object']).isRequired,
      properties: PropTypes.shape({
        authenticationAttribute: PropTypes.exact({
          type: PropTypes.oneOf(['string']).isRequired,
          title: PropTypes.string.isRequired,
          description: PropTypes.string.isRequired,
          enum: PropTypes.arrayOf(PropTypes.string).isRequired,
          enumNames: PropTypes.arrayOf(PropTypes.string).isRequired,
        }).isRequired,
        additionalScopes: PropTypes.exact({
          type: PropTypes.oneOf(['array']).isRequired,
          title: PropTypes.string.isRequired,
          description: PropTypes.string.isRequired,
          items: PropTypes.exact({
            type: PropTypes.oneOf(['string']).isRequired,
            enum: PropTypes.arrayOf(PropTypes.string).isRequired,
            enumNames: PropTypes.arrayOf(PropTypes.string).isRequired,
          }),
        }).isRequired,
      }),
      anyOf: PropTypes.oneOfType([
        PropTypes.shape({
          type: PropTypes.oneOf(['object']).isRequired,
          properties: PropTypes.shape({
            loa: PropTypes.exact({
              type: PropTypes.oneOf(['string']).isRequired,
              title: PropTypes.string.isRequired,
              description: PropTypes.string.isRequired,
              enum: PropTypes.arrayOf(PropTypes.string).isRequired,
              enumNames: PropTypes.arrayOf(PropTypes.string).isRequired,
            }),
          }),
        }),
      ]),
      discriminator: PropTypes.shape({
        bsn: PropTypes.shape({
          type: PropTypes.oneOf(['object']).isRequired,
          properties: PropTypes.shape({
            loa: PropTypes.exact({
              type: PropTypes.oneOf(['string']).isRequired,
              title: PropTypes.string.isRequired,
              description: PropTypes.string.isRequired,
              enum: PropTypes.arrayOf(PropTypes.string).isRequired,
              enumNames: PropTypes.arrayOf(PropTypes.string).isRequired,
            }),
          }),
        }),
      }),
    }),
  }),
};

export default YiviOptionsFormFields;
