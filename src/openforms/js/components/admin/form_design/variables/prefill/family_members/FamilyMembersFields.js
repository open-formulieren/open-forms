import {useFormikContext} from 'formik';
import {useContext, useEffect} from 'react';

import ValidationErrorsProvider, {
  ValidationErrorContext,
} from 'components/admin/forms/ValidationErrors';

import ChildrenFiltersFields from './ChildrenFiltersFields';
import PersonFields from './PersonsFields';

const FamilyMembersFields = () => {
  const {values, setFieldValue} = useFormikContext();

  const {
    options: {type},
  } = values;

  const errors = Object.fromEntries(useContext(ValidationErrorContext));
  const optionsErrors = Object.entries(errors.options ?? {}).map(([key, errs]) => [
    `options.${key}`,
    errs,
  ]);

  const defaults = {
    mutableDataFormVariable: '',
    type: null,
    minAge: null,
    maxAge: null,
    includeDeceased: true,
  };

  //   Merge defaults into options if not already set
  useEffect(() => {
    const options = values.options ?? {};
    setFieldValue('options', {...defaults, ...options});
  }, []);

  const showFilters = type === 'children';

  return (
    <ValidationErrorsProvider errors={optionsErrors}>
      <PersonFields />
      {showFilters && <ChildrenFiltersFields />}
    </ValidationErrorsProvider>
  );
};

export default FamilyMembersFields;
