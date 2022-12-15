import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage, useIntl} from 'react-intl';

import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';

import {FormContext} from './Context';
import LanguageTabs from './LanguageTabs';

const TextLiterals = ({onChange, translations}) => {
  return (
    <Fieldset>
      <LanguageTabs>
        {langCode => (
          <>
            <FormRow>
              <Field
                name={`form.translations.${langCode}.beginText`}
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
                  value={translations[langCode].beginText}
                  onChange={onChange}
                  maxLength="50"
                />
              </Field>
            </FormRow>
            <FormRow>
              <Field
                name={`form.translations.${langCode}.previousText`}
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
                  value={translations[langCode].previousText}
                  onChange={onChange}
                  maxLength="50"
                />
              </Field>
            </FormRow>
            <FormRow>
              <Field
                name={`form.translations.${langCode}.changeText`}
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
                  value={translations[langCode].changeText}
                  onChange={onChange}
                  maxLength="50"
                />
              </Field>
            </FormRow>
            <FormRow>
              <Field
                name={`form.translations.${langCode}.confirmText`}
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
                  value={translations[langCode].confirmText}
                  onChange={onChange}
                  maxLength="50"
                />
              </Field>
            </FormRow>
          </>
        )}
      </LanguageTabs>
    </Fieldset>
  );
};

TextLiterals.propTypes = {
  onChange: PropTypes.func.isRequired,
  translations: PropTypes.object,
};

export default TextLiterals;
