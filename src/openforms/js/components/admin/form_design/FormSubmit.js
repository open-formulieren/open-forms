import PropTypes from 'prop-types';
import React, {useRef, useState} from 'react';
import {useIntl} from 'react-intl';

import ActionButton from 'components/admin/forms/ActionButton';
import SubmitRow from 'components/admin/forms/SubmitRow';
import ExportOptionsModal from 'components/admin/import_export/ExportOptionsModal';
import {serializeExportOptions} from 'components/admin/import_export/utils';

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
  const [isModalOpen, setIsModalOpen] = useState(false);
  const exportButtonRef = useRef(null);
  const exportOptionsRef = useRef(null);

  const intl = useIntl();
  const btnText = intl.formatMessage({
    defaultMessage: 'Export',
    description: 'Export form button',
  });
  const btnTitle = intl.formatMessage({
    defaultMessage: 'Export this form',
    description: 'Export form button title',
  });

  return (
    <>
      <input ref={exportButtonRef} type="submit" name="_export" hidden />
      <input ref={exportOptionsRef} type="hidden" name="export_options" />
      <ActionButton
        text={btnText}
        title={btnTitle}
        type="button"
        onClick={() => setIsModalOpen(true)}
      />
      <ExportOptionsModal
        isOpen={isModalOpen}
        onSubmit={exportOptions => {
          exportOptionsRef.current.value = JSON.stringify(serializeExportOptions(exportOptions));
          exportButtonRef.current.click();
        }}
        onCloseModal={() => setIsModalOpen(false)}
      />
    </>
  );
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
