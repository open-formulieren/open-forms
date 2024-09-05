import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {FormattedMessage} from 'react-intl';

import MessageList from 'components/admin/MessageList';
import TYPES from 'components/admin/form_design/types';
import {Modal} from 'components/admin/modals';
import {ChangelistColumn, ChangelistTable} from 'components/admin/tables';
import jsonScriptToVar from 'utils/json-script';

const LABEL_MAPPING = jsonScriptToVar('label-mapping', {default: {}});
const LANGUAGES = jsonScriptToVar('languages', {default: []});

const extractMissingTranslations = (
  translations,
  tabName,
  fieldNames,
  fallbackFields,
  optionalFields = []
) => {
  const defaultLangCode = LANGUAGES[0][0];
  const languageCodeMapping = Object.fromEntries(LANGUAGES);
  let skipWarningsFor = [];
  const numOptionalTranslations = {};

  const numLanguages = Object.keys(translations).length;
  // count the amount of optional field translations
  for (const [languageCode, mapping] of Object.entries(translations)) {
    for (const [key, translation] of Object.entries(mapping)) {
      if (fieldNames && fieldNames.includes(key) && optionalFields.includes(key)) {
        if (!numOptionalTranslations[key]) numOptionalTranslations[key] = 0;
        if (translation) numOptionalTranslations[key] += 1;
      }
    }
  }

  let missingTranslations = [];
  for (const [languageCode, mapping] of Object.entries(translations)) {
    for (const [key, translation] of Object.entries(mapping)) {
      // Ignore missing translations for fields that can have global defaults,
      // if no value was entered for the default
      if (!translation && languageCode === defaultLangCode && (fallbackFields || []).includes(key))
        skipWarningsFor.push(key);

      // Ignore optional fields that are all empty or filled in
      if (numOptionalTranslations[key] === 0 || numOptionalTranslations[key] === numLanguages)
        skipWarningsFor.push(key);

      if (translation) continue;
      if (skipWarningsFor.includes(key)) continue;
      if (fieldNames && !fieldNames.includes(key)) continue;

      missingTranslations.push({
        fieldName: LABEL_MAPPING[key],
        language: languageCodeMapping[languageCode],
        tabName: tabName,
      });
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

  for (const formStep of formSteps) {
    formStepTranslations = formStepTranslations.concat(
      extractMissingTranslations(
        formStep.translations,
        <FormattedMessage defaultMessage="Steps and fields" description="Form design tab title" />,
        undefined,
        ['previousText', 'saveText', 'nextText']
      )
    );
  }

  const missingTranslations = [].concat(
    extractMissingTranslations(
      form.translations,
      <FormattedMessage defaultMessage="Form" description="Form fields tab title" />,
      ['name', 'introductionPageContent', 'explanationTemplate'],
      undefined,
      ['introductionPageContent', 'explanationTemplate']
    ),
    extractMissingTranslations(
      form.translations,
      <FormattedMessage
        defaultMessage="Confirmation"
        description="Form confirmation options tab title"
      />,
      ['submissionConfirmationTemplate'],
      ['submissionConfirmationTemplate']
    ),
    extractMissingTranslations(
      form.translations,
      <FormattedMessage defaultMessage="Literals" description="Form literals tab title" />,
      ['beginText', 'previousText', 'changeText', 'confirmText'],
      ['beginText', 'previousText', 'changeText', 'confirmText']
    ),
    extractMissingTranslations(
      form.confirmationEmailTemplate.translations,
      <FormattedMessage
        defaultMessage="Confirmation"
        description="Form confirmation options tab title"
      />,
      undefined,
      ['subject', 'content']
    ),
    formStepTranslations
  );

  const [modalOpen, setModalOpen] = useState(false);

  const onShowModal = event => {
    event.preventDefault();
    setModalOpen(true);
  };

  let warningList = [];
  if (missingTranslations.length) {
    let formattedWarning = (
      <FormattedMessage
        description="Warning message for missing translations"
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
    warningList.push({level: 'warning', message: formattedWarning});
  }

  if (!warningList.length) {
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

      <MessageList messages={warningList} />
    </>
  );
};

MissingTranslationsWarning.propTypes = {
  form: PropTypes.object.isRequired,
  formSteps: PropTypes.arrayOf(TYPES.FormStep).isRequired,
};

export default MissingTranslationsWarning;
