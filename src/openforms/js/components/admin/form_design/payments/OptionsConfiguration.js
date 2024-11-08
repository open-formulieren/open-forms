import {Formik} from 'formik';
import PropTypes from 'prop-types';
import {useState} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import {SubmitAction} from 'components/admin/forms/ActionButton';
import Field from 'components/admin/forms/Field';
import ModalOptionsConfiguration from 'components/admin/forms/ModalOptionsConfiguration';
import SubmitRow from 'components/admin/forms/SubmitRow';
import {ErrorIcon} from 'components/admin/icons';
import {FormModal} from 'components/admin/modals';

const OptionsConfiguration = ({numErrors, modalTitle, initialFormData, onSubmit, children}) => (
  <ModalOptionsConfiguration
    name="form.paymentBackendOptions"
    label={
      <FormattedMessage
        description="Payment backend options label"
        defaultMessage="Payment backend options"
      />
    }
    numErrors={numErrors}
    modalTitle={modalTitle}
    initialFormData={initialFormData}
    onSubmit={onSubmit}
    modalSize=""
    children={children}
  />
);

OptionsConfiguration.propTypes = {
  modalTitle: PropTypes.node.isRequired,
  numErrors: PropTypes.number.isRequired,
  initialFormData: PropTypes.object.isRequired,
  onSubmit: PropTypes.func.isRequired,
};

export default OptionsConfiguration;
