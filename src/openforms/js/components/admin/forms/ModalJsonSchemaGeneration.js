import {JSONEditor} from '@open-formulieren/monaco-json-editor';
// TODO-5312: is it OK to install this package or better to create a custom component? I also see
//  it's installed under devDependencies, so it won't be available in production?
import {ButtonLink} from '@utrecht/component-library-react';
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
const ModalJsonSchemaGeneration = ({modalTitle, pluginId, modalSize = 'large'}) => {
  const [modalOpen, setModalOpen] = useState(false);
  const [hasError, setErrorState] = useState(false);
  const [schema, setSchema] = useState(null);
  const [theme] = useGlobalState(currentTheme);
  const {form} = useContext(FormContext);

  async function onClick() {
    setModalOpen(true);
    const params = new URLSearchParams({registration_plugin_id: pluginId});
    const response = await get(`${FORM_ENDPOINT}/${form.uuid}/json_schema?${params}`);
    if (!response.ok) {
      setErrorState(true);
    }
    setSchema(response.data);
  }

  return (
    <>
      <ButtonLink onClick={onClick} style={{color: 'var(--link-fg)', cursor: 'pointer'}}>
        <FormattedMessage
          description="Link label to generate JSON schema of registration backend"
          defaultMessage="Generate JSON schema"
        />
      </ButtonLink>

      <Modal
        isOpen={modalOpen}
        title={modalTitle}
        closeModal={() => setModalOpen(false)}
        contentModifiers={modalSize ? [modalSize] : undefined}
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
  pluginId: PropTypes.string.isRequired,
  modalSize: PropTypes.oneOf(['', 'small', 'large']),
};

export default ModalJsonSchemaGeneration;
