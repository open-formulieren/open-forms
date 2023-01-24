import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {FormattedMessage} from 'react-intl';

import MessageList from 'components/admin/MessageList';
import Modal from 'components/admin/Modal';
import {ChangelistColumn, ChangelistTable} from 'components/admin/tables';
import jsonScriptToVar from 'utils/json-script';

const extractMissingTranslations = (translations, tabName, fieldNames) => {
  const labelMapping = jsonScriptToVar('label-mapping');
  const languages = jsonScriptToVar('languages');
  const languageCodeMapping = Object.fromEntries(languages);

  let missingTranslations = [];
  for (const [languageCode, mapping] of Object.entries(translations)) {
    for (const [key, translation] of Object.entries(mapping)) {
      if (!translation) {
        if (fieldNames === undefined) {
          missingTranslations.push({
            fieldName: labelMapping[key],
            language: languageCodeMapping[languageCode],
            tabName: tabName,
          });
        } else if (fieldNames.includes(key)) {
          missingTranslations.push({
            fieldName: labelMapping[key],
            language: languageCodeMapping[languageCode],
            tabName: tabName,
          });
        }
      }
    }
  }
  return missingTranslations;
};

const MissingTranslationsTable = ({children: missingTranslations}) => (
  <ChangelistTable data={missingTranslations}>
    <ChangelistColumn objProp="tabName">
      <FormattedMessage description="Name of the tab in the Form admin" defaultMessage="Tab name" />
    </ChangelistColumn>

    <ChangelistColumn objProp="language">
      <FormattedMessage description="Readable label for the language" defaultMessage="Language" />
    </ChangelistColumn>

    <ChangelistColumn objProp="fieldName">
      <FormattedMessage description="Name of the translatable field" defaultMessage="Field name" />
    </ChangelistColumn>
  </ChangelistTable>
);

MissingTranslationsTable.propTypes = {
  children: PropTypes.arrayOf(PropTypes.object),
};

const MissingTranslationsWarning = ({form, formSteps}) => {
  let formStepTranslations = [];

  for (const [index, formStep] of formSteps.entries()) {
    formStepTranslations = formStepTranslations.concat(
      extractMissingTranslations(
        formStep.translations,
        <FormattedMessage defaultMessage="Steps and fields" description="Form design tab title" />
      )
    );
  }

  const missingTranslations = [].concat(
    extractMissingTranslations(
      form.translations,
      <FormattedMessage defaultMessage="Form" description="Form fields tab title" />,
      ['name', 'explanationTemplate']
    ),
    extractMissingTranslations(
      form.translations,
      <FormattedMessage
        defaultMessage="Confirmation"
        description="Form confirmation options tab title"
      />,
      ['submissionConfirmationTemplate']
    ),
    extractMissingTranslations(
      form.translations,
      <FormattedMessage defaultMessage="Literals" description="Form literals tab title" />,
      ['beginText', 'previousText', 'changeText', 'confirmText']
    ),
    extractMissingTranslations(
      form.confirmationEmailTemplate.translations,
      <FormattedMessage
        defaultMessage="Confirmation"
        description="Form confirmation options tab title"
      />
    ),
    formStepTranslations
  );

  const [modalOpen, setModalOpen] = useState(false);

  const onShowModal = event => {
    event.preventDefault();
    setModalOpen(true);
  };

  const formattedWarning = (
    <FormattedMessage
      description="Translations are missing"
      defaultMessage="Form has translation enabled, but is missing <link>{count, plural,
        one {# translation}
        other {# translations}
    }</link>"
      values={{
        count: missingTranslations.length,
        link: chunks => (
          <a href="#" onClick={onShowModal}>
            {chunks}
          </a>
        ),
      }}
    />
  );

  if (!missingTranslations.length) {
    return null;
  }

  return (
    <>
      <Modal
        isOpen={modalOpen}
        closeModal={() => setModalOpen(false)}
        title={`Missing translations`}
      >
        <MissingTranslationsTable>{missingTranslations}</MissingTranslationsTable>
      </Modal>

      <MessageList messages={[{level: 'warning', message: formattedWarning}]} />
    </>
  );
};

MissingTranslationsWarning.propTypes = {
  form: PropTypes.object.isRequired,
  formSteps: PropTypes.array.isRequired,
};

export default MissingTranslationsWarning;
