import {useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {useContext, useEffect} from 'react';

import {
  ValidationErrorContext,
  ValidationErrorsProvider,
  filterErrors,
} from 'components/admin/forms/ValidationErrors';

import VisibleField from './VisibleField';

const OrgOidcOptionsFormFields = ({name}) => {
  const validationErrors = useContext(ValidationErrorContext);
  const relevantErrors = filterErrors(name, validationErrors);

  // set defaults
  const {values, setValues} = useFormikContext();
  const defaults = {
    visible: true,
  };

  //   Merge defaults into options if not already set
  useEffect(() => {
    setValues(prevValues => ({...defaults, ...prevValues}));
  }, []);

  return (
    <ValidationErrorsProvider errors={relevantErrors}>
      <VisibleField />
    </ValidationErrorsProvider>
  );
};

OrgOidcOptionsFormFields.propType = {
  name: PropTypes.string.isRequired,
};

export default OrgOidcOptionsFormFields;
