import {useFormikContext} from 'formik';
import PropTypes from 'prop-types';
import {useContext, useState} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import {FormContext} from 'components/admin/form_design/Context';
import useConfirm from 'components/admin/form_design/useConfirm';
import {ChangelistTableWrapper, HeadColumn} from 'components/admin/tables';

const CopyDocumentTypesConfig = ({catalogueField, descriptionField}) => {
  const intl = useIntl();
  const {components, updateComponents} = useContext(FormContext);
  const {getFieldMeta} = useFormikContext();
  const [selectedComponents, setSelectedComponents] = useState([]);
  const {ConfirmationModal, confirmationModalProps, openConfirmationModal} = useConfirm();

  const fileComponents = Object.values(components).filter(component => component.type === 'file');
  const catalogue = getFieldMeta(catalogueField).value ?? {domain: '', rsin: ''};
  const description = getFieldMeta(descriptionField).value ?? '';

  if (!fileComponents.length)
    return (
      <div className="form-row">
        <p>
          <FormattedMessage
            description="Copy document types config: no file components text"
            defaultMessage="There are no file upload components in the form."
          />
        </p>
      </div>
    );

  const componentTableHeadColumns = [
    <HeadColumn
      key="checkbox"
      content={
        <input
          type="checkbox"
          checked={selectedComponents.length === fileComponents.length}
          onChange={event => {
            const {checked} = event.target;
            setSelectedComponents(checked ? fileComponents.map(c => c.key) : []);
          }}
          aria-label={intl.formatMessage({
            description: 'Accessible label for check/uncheck all file components',
            defaultMessage: 'Check/uncheck all',
          })}
        />
      }
    />,
    <HeadColumn
      key="label"
      content={
        <FormattedMessage
          description="Copy document types config to file components: component label heading"
          defaultMessage="Field label"
        />
      }
    />,
    <HeadColumn
      key="domain"
      content={
        <FormattedMessage
          description="Copy document types config to file components: catalogue domain heading"
          defaultMessage="Catalogue domain"
        />
      }
    />,
    <HeadColumn
      key="rsin"
      content={
        <FormattedMessage
          description="Copy document types config to file components: catalogue RSIN heading"
          defaultMessage="Catalogue RSIN"
        />
      }
    />,
    <HeadColumn
      key="description"
      content={
        <FormattedMessage
          description="Copy document types config to file components: doc type description heading"
          defaultMessage="Document type description"
        />
      }
    />,
  ];

  return (
    <>
      <div className="description">
        <FormattedMessage
          description="Copy document types config: feature description"
          defaultMessage={`You can copy the catalogue and document type description
          from the plugin options to the selected file upload fields of the form. Note
          that this will overwrite existing field-level configuration!`}
        />
      </div>
      <div className="form-row">
        <ChangelistTableWrapper headColumns={componentTableHeadColumns}>
          {fileComponents.map(component => (
            <tr key={component.key}>
              <td style={{padding: '8px 10px'}}>
                <input
                  type="checkbox"
                  checked={selectedComponents.includes(component.key)}
                  onChange={event => {
                    const {key} = component;
                    const {checked} = event.target;
                    const updatedSelectedComponents = checked
                      ? [...selectedComponents, key]
                      : selectedComponents.filter(k => k !== key);
                    setSelectedComponents(updatedSelectedComponents);
                  }}
                  aria-label={intl.formatMessage(
                    {
                      description: 'Accessible label for check/uncheck single file component',
                      defaultMessage: 'Update {label} configuration?',
                    },
                    {label: component.label}
                  )}
                />
              </td>
              <td>{component.label}</td>
              <td>{component?.registration?.documentType?.catalogue?.domain ?? '-'}</td>
              <td>{component?.registration?.documentType?.catalogue?.rsin ?? '-'}</td>
              <td>{component?.registration?.documentType?.description ?? '-'}</td>
            </tr>
          ))}
        </ChangelistTableWrapper>

        <div style={{textAlign: 'end'}}>
          <button
            type="button"
            className="button"
            disabled={selectedComponents.length === 0}
            onClick={async () => {
              const confirm = await openConfirmationModal();
              if (!confirm) return;
              updateComponents(selectedComponents, componentDraft => {
                if (!componentDraft.registration) {
                  componentDraft.registration = {};
                }
                if (!componentDraft.registration.documentType) {
                  componentDraft.registration.documentType = {};
                }
                componentDraft.registration.documentType.catalogue = catalogue;
                componentDraft.registration.documentType.description = description;
                setSelectedComponents([]);
              });
            }}
            style={{paddingInline: '15px', paddingBlock: '10px'}}
          >
            <FormattedMessage
              description="Copy document types config: copy button label"
              defaultMessage="Copy"
            />
          </button>
        </div>
      </div>

      <ConfirmationModal
        {...confirmationModalProps}
        message={
          <FormattedMessage
            description="Copy document type configuration to selected file components confirmation modal content"
            defaultMessage="The file component changes will be applied immediately. Are you sure you want to continue?"
          />
        }
      />
    </>
  );
};

CopyDocumentTypesConfig.propTypes = {
  catalogueField: PropTypes.string.isRequired,
  descriptionField: PropTypes.string.isRequired,
};

export default CopyDocumentTypesConfig;
