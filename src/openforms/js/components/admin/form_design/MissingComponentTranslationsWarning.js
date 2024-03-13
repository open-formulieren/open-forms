import FormioUtils from 'formiojs/utils';
import PropTypes from 'prop-types';
import React, {useState} from 'react';
import {FormattedMessage} from 'react-intl';

import MessageList from 'components/admin/MessageList';
import {Modal} from 'components/admin/modals';
import {ChangelistColumn, ChangelistTable} from 'components/admin/tables';
import {
  extractComponentLiterals,
  getSupportedLanguages,
} from 'components/formio_builder/translation';

const LANGUAGES = getSupportedLanguages();

const extractTranslatableProperties = configuration => {
  let translatableValues = [];
  FormioUtils.eachComponent(
    configuration.components,
    component => {
      const literals = extractComponentLiterals(component);
      literals.forEach(literal => {
        translatableValues.push({
          component: component,
          componentKey: component.key,
          componentLabel: component.label,
          literal: literal.literal,
          property: literal.property,
        });
      });
    },
    true
  );
  return translatableValues;
};
const extractMissingComponentTranslations = configuration => {
  const languageCodeMapping = Object.fromEntries(LANGUAGES);

  const translatableProperties = extractTranslatableProperties(configuration);

  let missingTranslations = [];
  for (const entry of translatableProperties) {
    const component = entry.component;

    for (const [languageCode, _languageLabel] of LANGUAGES) {
      let translations = component.openForms?.translations?.[languageCode] || {};

      if (!translations[entry.property])
        missingTranslations.push({language: languageCodeMapping[languageCode], ...entry});
    }
  }
  missingTranslations.sort((a, b) => {
    if (a.componentKey !== b.componentKey) {
      return a.componentKey.localeCompare(b.componentKey);
    }
    if (a.language !== b.language) {
      return a.language.localeCompare(b.language);
    }
    return a.literal.localeCompare(b.literal);
  });

  return missingTranslations;
};

const MissingComponentTranslationsTable = ({children: missingTranslations}) => (
  <ChangelistTable data={missingTranslations}>
    <ChangelistColumn objProp="componentKey">
      <FormattedMessage description="Key of the Form component" defaultMessage="Component key" />
    </ChangelistColumn>

    <ChangelistColumn objProp="componentLabel">
      <FormattedMessage
        description="Label of the Form component"
        defaultMessage="Component label"
      />
    </ChangelistColumn>

    <ChangelistColumn objProp="language">
      <FormattedMessage description="Readable label for the language" defaultMessage="Language" />
    </ChangelistColumn>

    <ChangelistColumn objProp="literal">
      <FormattedMessage description="Literal to be translated" defaultMessage="Literal" />
    </ChangelistColumn>
  </ChangelistTable>
);

MissingComponentTranslationsTable.propTypes = {
  children: PropTypes.arrayOf(
    PropTypes.shape({
      component: PropTypes.object.isRequired,
      componentKey: PropTypes.string.isRequired,
      componentLabel: PropTypes.string.isRequired,
      language: PropTypes.string.isRequired,
      literal: PropTypes.string.isRequired,
    })
  ),
};

const MissingComponentTranslationsWarning = ({configuration}) => {
  const [modalOpen, setModalOpen] = useState(false);

  const onShowModal = event => {
    event.preventDefault();
    setModalOpen(true);
  };

  const missingTranslations = extractMissingComponentTranslations(configuration);

  const formattedWarning = (
    <FormattedMessage
      description="Warning message for missing component translations"
      defaultMessage="Form has translation enabled, but is missing <link>{count, plural,
        one {# component translation}
        other {# component translations}
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
        <MissingComponentTranslationsTable>{missingTranslations}</MissingComponentTranslationsTable>
      </Modal>

      <MessageList messages={[{level: 'warning', message: formattedWarning}]} />
    </>
  );
};

MissingComponentTranslationsWarning.propTypes = {
  configuration: PropTypes.object.isRequired,
};

export default MissingComponentTranslationsWarning;
export {extractMissingComponentTranslations};
