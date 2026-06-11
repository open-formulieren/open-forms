import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import {TargetPathSelect} from 'components/admin/forms/objects_api';

const TargetPath = ({namePrefix, loading, targetPaths, isDisabled = false}) => (
  <FormRow>
    <Field
      name={`${namePrefix}.targetPath`}
      label={
        <FormattedMessage
          defaultMessage="JSON Schema target"
          description="'JSON Schema target' label"
        />
      }
      required
      disabled={isDisabled}
      noManageChildProps
    >
      <TargetPathSelect
        name={`${namePrefix}.targetPath`}
        isLoading={loading}
        targetPaths={targetPaths}
        isDisabled={isDisabled}
      />
    </Field>
  </FormRow>
);

export default TargetPath;
