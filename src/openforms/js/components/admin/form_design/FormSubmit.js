import PropTypes from 'prop-types';
import React from 'react';
import {useIntl} from 'react-intl';

import ActionButton from 'components/admin/forms/ActionButton';
import SubmitRow from 'components/admin/forms/SubmitRow';

const CopyAction = () => {
  const intl = useIntl();
  const btnText = intl.formatMessage({
    defaultMessage: 'Copy',
    description: 'Copy form button',
  });
  const btnTitle = intl.formatMessage({
    defaultMessage: 'Duplicate this form',
    description: 'Copy form button title',
  });
  return <ActionButton name="_copy" text={btnText} title={btnTitle} />;
};

const ExportAction = () => {
  const intl = useIntl();
  const btnText = intl.formatMessage({
    defaultMessage: 'Export',
    description: 'Export form button',
  });
  const btnTitle = intl.formatMessage({
    defaultMessage: 'Export this form',
    description: 'Export form button title',
  });
  return <ActionButton name="_export" text={btnText} title={btnTitle} />;
};

const FormSubmit = ({onSubmit, displayActions = false}) => (
  <>
    <SubmitRow onSubmit={onSubmit} isDefault />
    {displayActions ? (
      <SubmitRow extraClassName="submit-row-extended">
        <CopyAction />
        <ExportAction />
      </SubmitRow>
    ) : null}
  </>
);

FormSubmit.propTypes = {
  onSubmit: PropTypes.func.isRequired,
  displayActions: PropTypes.bool,
};

export default FormSubmit;
