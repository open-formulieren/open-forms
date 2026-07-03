import PropTypes from 'prop-types';
import React, {useEffect, useRef, useState} from 'react';
import {useIntl} from 'react-intl';

import ExportOptionsModal from 'components/admin/form_export/ExportOptionsModal';
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

// Convert camelCase export options to snake_case, for API compatibility.
const serializeExportOptions = exportOptions => ({
  remove_sensitive_content: exportOptions.removeSensitiveContent,
  form_configuration: exportOptions.formConfiguration,
  additional_form_configuration: exportOptions.additionalFormConfiguration,
});

const ExportAction = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [exportOptions, setExportOptions] = useState(null);
  const exportButtonRef = useRef(null);

  const intl = useIntl();
  const btnText = intl.formatMessage({
    defaultMessage: 'Export',
    description: 'Export form button',
  });
  const btnTitle = intl.formatMessage({
    defaultMessage: 'Export this form',
    description: 'Export form button title',
  });

  useEffect(() => {
    if (exportOptions !== null) {
      // click the hidden export button to trigger the backend form configuration export
      exportButtonRef.current?.click();
      setExportOptions(null);
    }
  }, [exportOptions, setExportOptions]);

  return (
    <>
      <input ref={exportButtonRef} type="submit" name="_export" hidden />
      <input
        type="hidden"
        name="export_options"
        defaultValue={
          exportOptions !== null ? JSON.stringify(serializeExportOptions(exportOptions)) : '{}'
        }
      />
      <ActionButton
        text={btnText}
        title={btnTitle}
        type="button"
        onClick={() => setIsModalOpen(true)}
      />
      <ExportOptionsModal
        isOpen={isModalOpen}
        onSubmit={newExportOptions => setExportOptions(newExportOptions)}
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
