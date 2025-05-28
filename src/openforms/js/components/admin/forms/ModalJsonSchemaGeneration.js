import {JSONEditor} from '@open-formulieren/monaco-json-editor';
import PropTypes from 'prop-types';
import {React, useContext, useState} from 'react';
import {FormattedMessage} from 'react-intl';
import {useGlobalState} from 'state-pool';

import {FormContext} from 'components/admin/form_design/Context';
import {FORM_ENDPOINT} from 'components/admin/form_design/constants';
import Modal from 'components/admin/modals/Modal';
import ErrorMessage from 'components/errors/ErrorMessage';
import {get} from 'utils/fetch';
import {currentTheme} from 'utils/theme';

/**
 * A container for JSON schema generation of a form.
 */
const ModalJsonSchemaGeneration = ({modalTitle, backendKey}) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [hasError, setErrorState] = useState(false);
  const [schema, setSchema] = useState(null);
  const [theme] = useGlobalState(currentTheme);
  const {form} = useContext(FormContext);

  async function onShowModal() {
    setModalOpen(true);
    const response = await get(`${FORM_ENDPOINT}/${form.uuid}/json_schema`, {
      registration_backend_key: backendKey,
    });
    if (!response.ok) {
      setErrorState(true);
      setSchema(null);
    }
    setSchema(response.data);
  }

  return (
    <>
      <button
        type="button"
        onClick={onShowModal}
        className="button button--link"
        style={{paddingBlock: '5px', paddingInline: '0px'}}
      >
        <FormattedMessage
          description="Link label to generate JSON schema of registration backend"
          defaultMessage="Generate JSON schema"
        />
      </button>

      <Modal
        isOpen={modalOpen}
        title={modalTitle}
        closeModal={() => setModalOpen(false)}
        contentModifiers={['large']}
      >
        {hasError && (
          <ErrorMessage>
            <FormattedMessage
              description="Form schema generation error message"
              defaultMessage="An error occurred during schema generation"
            />
          </ErrorMessage>
        )}

        {schema && <JSONEditor value={schema} theme={theme} readOnly showLines />}
      </Modal>
    </>
  );
};

ModalJsonSchemaGeneration.propTypes = {
  modalTitle: PropTypes.node.isRequired,
  backendKey: PropTypes.string.isRequired,
  modalSize: PropTypes.oneOf(['', 'small', 'large']),
};

export default ModalJsonSchemaGeneration;
