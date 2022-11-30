import React, {useContext} from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage, useIntl} from 'react-intl';
import {Tabs, TabList, TabPanel} from 'react-tabs';

import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';

import {FormContext} from './Context';
import Tab from './Tab';

const activeTab = new URLSearchParams(window.location.search).get('tab');

const TextLiterals = ({onChange, translations}) => {
  const {languages} = useContext(FormContext);
  let tabs = languages.map((language, index) => {
    return <Tab key={language.code}>{language.code}</Tab>;
  });

  let tabPanels = languages.map((language, index) => {
    const langCode = language.code;
    return (
      <TabPanel key={langCode}>
        <FormRow>
          <Field
            name={`literals.translations.${langCode}.beginText`}
            label={
              <FormattedMessage
                description="literals.beginText form label"
                defaultMessage="Begin text"
              />
            }
            helpText={
              <FormattedMessage
                description="literals.beginText help text"
                defaultMessage="The text that will be displayed at the start of the form to indicate the user can begin to fill in the form. Leave blank to get value from global configuration."
              />
            }
          >
            <TextInput
              value={translations[langCode].beginText.value}
              onChange={onChange}
              maxLength="50"
            />
          </Field>
        </FormRow>
        <FormRow>
          <Field
            name={`literals.translations.${langCode}.previousText`}
            label={
              <FormattedMessage
                description="literals.previousText form label"
                defaultMessage="Previous text"
              />
            }
            helpText={
              <FormattedMessage
                description="literals.previousText help text"
                defaultMessage="The text that will be displayed in the overview page to go to the previous step. Leave blank to get value from global configuration."
              />
            }
          >
            <TextInput
              value={translations[langCode].previousText.value}
              onChange={onChange}
              maxLength="50"
            />
          </Field>
        </FormRow>
        <FormRow>
          <Field
            name={`literals.translations.${langCode}.changeText`}
            label={
              <FormattedMessage
                description="literals.changeText form label"
                defaultMessage="Change text"
              />
            }
            helpText={
              <FormattedMessage
                description="literals.changeText help text"
                defaultMessage="The text that will be displayed in the overview page to change a certain step. Leave blank to get value from global configuration."
              />
            }
          >
            <TextInput
              value={translations[langCode].changeText.value}
              onChange={onChange}
              maxLength="50"
            />
          </Field>
        </FormRow>
        <FormRow>
          <Field
            name={`literals.translations.${langCode}.confirmText`}
            label={
              <FormattedMessage
                description="literals.confirmText form label"
                defaultMessage="Confirm text"
              />
            }
            helpText={
              <FormattedMessage
                description="literals.confirmText help text"
                defaultMessage="The text that will be displayed in the overview page to confirm the form is filled in correctly. Leave blank to get value from global configuration."
              />
            }
          >
            <TextInput
              value={translations[langCode].confirmText.value}
              onChange={onChange}
              maxLength="50"
            />
          </Field>
        </FormRow>
      </TabPanel>
    );
  });

  return (
    <Fieldset>
      <Tabs defaultIndex={activeTab ? parseInt(activeTab, 10) : null}>
        <TabList>{tabs}</TabList>

        {tabPanels}
      </Tabs>
    </Fieldset>
  );
};

TextLiterals.propTypes = {
  onChange: PropTypes.func.isRequired,
  translations: PropTypes.object,
};

export default TextLiterals;
