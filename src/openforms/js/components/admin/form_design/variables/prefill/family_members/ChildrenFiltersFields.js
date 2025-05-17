import {useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {Checkbox, NumberInput} from 'components/admin/forms/Inputs';

const ChildrenFiltersFields = ({minAge, maxAge, includeDeceased}) => {
  const {setFieldValue} = useFormikContext();

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
            value={minAge ?? ''}
            min={0}
            step={1}
            onChange={e => {
              setFieldValue('options.minAge', e.target.value);
            }}
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
            value={maxAge ?? ''}
            min={0}
            step={1}
            onChange={e => {
              setFieldValue('options.maxAge', e.target.value);
            }}
          />
        </Field>
      </FormRow>
      <FormRow>
        <Checkbox
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
          checked={includeDeceased ?? true}
          onChange={event => {
            setFieldValue('options.includeDeceased', event.target.checked);
          }}
        />
      </FormRow>
    </Fieldset>
  );
};

ChildrenFiltersFields.propTypes = {
  minAge: PropTypes.string,
  maxAge: PropTypes.string,
  includeDeceased: PropTypes.bool,
};

export default ChildrenFiltersFields;
