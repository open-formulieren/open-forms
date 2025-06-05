import {useFormikContext} from 'formik';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {Checkbox, NumberInput} from 'components/admin/forms/Inputs';

const ChildrenFiltersFields = () => {
  const {getFieldProps} = useFormikContext();

  return (
    <Fieldset
      title={
        <FormattedMessage
          description="Family members filters: fieldset title"
          defaultMessage="Filters"
        />
      }
    >
      <FormRow>
        <Field
          name="options.minAge"
          label={
            <FormattedMessage
              description="Family members filters: minimum age field label"
              defaultMessage="Minimum age"
            />
          }
          helpText={
            <FormattedMessage
              description="Family members filters: minimum age help text"
              defaultMessage="The minimum age used to determine which children will be displayed. 
                  Leave blank to show all children."
            />
          }
        >
          <NumberInput
            {...getFieldProps({name: 'options.minAge', type: 'number'})}
            min={0}
            step={1}
          />
        </Field>
      </FormRow>
      <FormRow>
        <Field
          name="options.maxAge"
          label={
            <FormattedMessage
              description="Family members filters: maximum age field label"
              defaultMessage="Maximum age"
            />
          }
          helpText={
            <FormattedMessage
              description="Family members filters: maximum age help text"
              defaultMessage="The maximum age used to determine which children will be displayed. 
                  Leave blank to show all children."
            />
          }
        >
          <NumberInput
            {...getFieldProps({name: 'options.maxAge', type: 'number'})}
            min={0}
            step={1}
          />
        </Field>
      </FormRow>
      <FormRow>
        <Checkbox
          {...getFieldProps({name: 'options.includeDeceased', type: 'checkbox'})}
          name="options.includeDeceased"
          label={
            <FormattedMessage
              description="Family members filters: include deceased label"
              defaultMessage="Include deceased"
            />
          }
          helpText={
            <FormattedMessage
              description="Family members filters: include deceased helpText"
              defaultMessage={`If enabled, any deceased children will be displayed too.`}
            />
          }
        />
      </FormRow>
    </Fieldset>
  );
};

export default ChildrenFiltersFields;
