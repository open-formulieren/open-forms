import {useField} from 'formik';
import {FormattedMessage} from 'react-intl';

import FormRow from 'components/admin/forms/FormRow';
import {Checkbox} from 'components/admin/forms/Inputs';

const SkipOwnershipCheck = () => {
  const [fieldProps] = useField({name: 'options.skipOwnershipCheck', type: 'checkbox'});
  return (
    <FormRow>
      <Checkbox
        label={
          <FormattedMessage
            description="Objects API registration: skipOwnershipCheck label"
            defaultMessage="Skip ownership check"
          />
        }
        helpText={
          <FormattedMessage
            description="Objects API registration: skipOwnershipCheck helpText"
            defaultMessage={`If enabled, then no access control on the referenced object is performed.
            Ensure that it does not contain private data before checking this!
          `}
          />
        }
        {...fieldProps}
      />
    </FormRow>
  );
};

SkipOwnershipCheck.propTypes = {};

export default SkipOwnershipCheck;
