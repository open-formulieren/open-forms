import {useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {useContext} from 'react';

import Fieldset from 'components/admin/forms/Fieldset';
import {
  ValidationErrorContext,
  ValidationErrorsProvider,
  filterErrors,
} from 'components/admin/forms/ValidationErrors';

import AdditionalAttributesGroupsField from './AdditionalAttributesGroupsField';
import AuthenticationOptionsField from './AuthenticationOptionsField';
import YiviOptionsFormBsnFields from './YiviOptionsFormBsnFields';
import YiviOptionsFormKvkFields from './YiviOptionsFormKvkFields';

const YiviOptionsFormFields = ({name, plugin}) => {
  const validationErrors = useContext(ValidationErrorContext);
  const {
    values: {authenticationOptions = []},
  } = useFormikContext();
  const relevantErrors = filterErrors(name, validationErrors);

  const showBsnFields = authenticationOptions.includes('bsn');
  const showKvkFields = authenticationOptions.includes('kvk');

  return (
    <ValidationErrorsProvider errors={relevantErrors}>
      <Fieldset>
        <AuthenticationOptionsField schema={plugin.schema} />
        <AdditionalAttributesGroupsField schema={plugin.schema} />
      </Fieldset>

      {showBsnFields && <YiviOptionsFormBsnFields plugin={plugin} />}
      {showKvkFields && <YiviOptionsFormKvkFields plugin={plugin} />}
    </ValidationErrorsProvider>
  );
};

YiviOptionsFormFields.propType = {
  name: PropTypes.string.isRequired,
  plugin: PropTypes.shape({
    id: PropTypes.string,
    label: PropTypes.string,
    providesAuth: PropTypes.arrayOf(PropTypes.string),
    schema: PropTypes.exact({
      type: PropTypes.oneOf(['object']).isRequired,
      properties: PropTypes.shape({
        authenticationOptions: PropTypes.exact({
          type: PropTypes.oneOf(['array']).isRequired,
          title: PropTypes.string.isRequired,
          description: PropTypes.string.isRequired,
          items: PropTypes.exact({
            type: PropTypes.oneOf(['string']).isRequired,
            enum: PropTypes.arrayOf(PropTypes.string).isRequired,
            enumNames: PropTypes.arrayOf(PropTypes.string).isRequired,
          }),
        }).isRequired,
        additionalAttributesGroups: PropTypes.exact({
          type: PropTypes.oneOf(['array']).isRequired,
          title: PropTypes.string.isRequired,
          description: PropTypes.string.isRequired,
          items: PropTypes.exact({
            type: PropTypes.oneOf(['string']).isRequired,
            enum: PropTypes.arrayOf(PropTypes.string).isRequired,
            enumNames: PropTypes.arrayOf(PropTypes.string).isRequired,
          }),
        }).isRequired,
        bsnLoa: PropTypes.exact({
          type: PropTypes.oneOf(['string']).isRequired,
          title: PropTypes.string.isRequired,
          description: PropTypes.string.isRequired,
          enum: PropTypes.arrayOf(PropTypes.string).isRequired,
          enumNames: PropTypes.arrayOf(PropTypes.string).isRequired,
        }),
        kvkLoa: PropTypes.exact({
          type: PropTypes.oneOf(['string']).isRequired,
          title: PropTypes.string.isRequired,
          description: PropTypes.string.isRequired,
          enum: PropTypes.arrayOf(PropTypes.string).isRequired,
          enumNames: PropTypes.arrayOf(PropTypes.string).isRequired,
        }),
      }),
    }),
  }),
};

export default YiviOptionsFormFields;
