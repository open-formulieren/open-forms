import PropTypes from 'prop-types';
import React, {useContext} from 'react';
import {FormattedMessage, defineMessage, useIntl} from 'react-intl';

import ErrorList from 'components/admin/forms/ErrorList';
import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {Checkbox, TextInput} from 'components/admin/forms/Inputs';
import Select from 'components/admin/forms/Select';
import {ValidationErrorContext} from 'components/admin/forms/ValidationErrors';
import {getTranslatedChoices} from 'utils/i18n';

import {FormContext} from './Context';
import TinyMCEEditor from './Editor';
import LanguageTabs from './LanguageTabs';
import {parseValidationErrors} from './utils';

const EMAIL_OPTIONS = [
  [
    'global_email',
    defineMessage({
      description: 'global_email option label',
      defaultMessage: 'Global email',
    }),
  ],
  [
    'form_specific_email',
    defineMessage({
      description: 'form_specific_email option label',
      defaultMessage: 'Form specific email',
    }),
  ],
  [
    'no_email',
    defineMessage({
      description: 'no_email option label',
      defaultMessage: 'No email',
    }),
  ],
];

const Confirmation = ({
  displayMainWebsiteLink = false,
  includeConfirmationPageContentInPdf = false,
  emailOption = 'global_email',
  emailTemplate = {},
  onChange,
  translations,
}) => {
  const intl = useIntl();
  const {languages} = useContext(FormContext);
  const allValidationErrors = useContext(ValidationErrorContext);
  const emailOptions = getTranslatedChoices(intl, EMAIL_OPTIONS);

  const onCheckboxChange = (event, currentValue) => {
    const {
      target: {name},
    } = event;
    onChange({target: {name, value: !currentValue}});
  };

  const formValidationErrors = parseValidationErrors(allValidationErrors, 'form');

  const erroredLanguages = {submission: [], email: []};
  const errorChecks = [
    {
      key: 'submission',
      container: formValidationErrors?.translations,
      fieldList: [
        'submissionConfirmationTemplate',
        'displayMainWebsiteLink',
        'includeConfirmationPageContentInPDF',
      ],
    },
    {
      key: 'email',
      container: formValidationErrors?.confirmationEmailTemplate?.translations,
      fieldList: ['subject', 'content', 'confirmationEmailOption', 'nonFieldErrors'],
    },
  ];

  errorChecks.forEach(({key, container, fieldList}) => {
    if (!container) return;
    Object.entries(container).forEach(([languageCode, errors]) => {
      Object.keys(errors).forEach(fieldName => {
        if (fieldList.includes(fieldName)) {
          erroredLanguages[key].push(languageCode);
          return;
        }
      });
    });
  });

  const emailTranslationErrors = formValidationErrors?.confirmationEmailTemplate?.translations;

  return (
    <div className="confirmation-page">
      <Fieldset
        title={
          <FormattedMessage
            defaultMessage="Submission confirmation template"
            description="Submission confirmation fieldset title"
          />
        }
      >
        <LanguageTabs haveErrors={erroredLanguages.submission} forceRenderTabPanel>
          {(langCode, defaultLang) => (
            <>
              <FormRow>
                <Field
                  name={`form.translations.${langCode}.submissionConfirmationTemplate`}
                  label={
                    <FormattedMessage
                      defaultMessage="Page content"
                      description="Confirmation page content label"
                    />
                  }
                  helpText={
                    <FormattedMessage
                      defaultMessage="The content of the submission confirmation page. It can contain variables that will be templated from the submitted form data. If not specified, the global template will be used."
                      description="Confirmation template help text"
                    />
                  }
                >
                  <TinyMCEEditor
                    content={translations[langCode].submissionConfirmationTemplate}
                    onEditorChange={(newValue, editor) =>
                      onChange({
                        target: {
                          name: `form.translations.${langCode}.submissionConfirmationTemplate`,
                          value: newValue,
                        },
                      })
                    }
                  />
                </Field>
              </FormRow>
              <FormRow>
                <Checkbox
                  name="form.displayMainWebsiteLink"
                  label={
                    <FormattedMessage
                      defaultMessage="Display main website link"
                      description="Display main website link field label"
                    />
                  }
                  helpText={
                    <FormattedMessage
                      defaultMessage="Whether to show a link to the main website on the confirmation page."
                      description="Display main website link help text"
                    />
                  }
                  checked={displayMainWebsiteLink}
                  onChange={event => onCheckboxChange(event, displayMainWebsiteLink)}
                  disabled={langCode !== defaultLang}
                />
              </FormRow>
              <FormRow>
                <Checkbox
                  name="form.includeConfirmationPageContentInPdf"
                  label={
                    <FormattedMessage
                      defaultMessage="Include confirmation page content in PDF"
                      description="Include confirmation page content in PDF"
                    />
                  }
                  helpText={
                    <FormattedMessage
                      defaultMessage="Whether to include the content of the confirmation page in the PDF."
                      description="Include confirmation page content in PDF"
                    />
                  }
                  checked={includeConfirmationPageContentInPdf}
                  onChange={event => onCheckboxChange(event, includeConfirmationPageContentInPdf)}
                />
              </FormRow>
            </>
          )}
        </LanguageTabs>
      </Fieldset>

      <Fieldset
        title={
          <FormattedMessage
            defaultMessage="Submission confirmation email template"
            description="Submission confirmation email fieldset title"
          />
        }
      >
        <LanguageTabs haveErrors={erroredLanguages.email} forceRenderTabPanel>
          {(langCode, defaultLang) => (
            <>
              {emailTranslationErrors?.[langCode]?.nonFieldErrors && (
                <ErrorList classNamePrefix="confirmation-page">
                  {emailTranslationErrors[langCode].nonFieldErrors}
                </ErrorList>
              )}
              <FormRow>
                <Field
                  name={`form.confirmationEmailTemplate.translations.${langCode}.subject`}
                  label={
                    <FormattedMessage
                      defaultMessage="Subject"
                      description="Confirmation Email Subject label"
                    />
                  }
                >
                  <TextInput
                    value={emailTemplate.translations[langCode].subject}
                    onChange={onChange}
                    maxLength="1000"
                  />
                </Field>
              </FormRow>
              <FormRow>
                <Field
                  name={`form.confirmationEmailTemplate.translations.${langCode}.content`}
                  label={
                    <FormattedMessage
                      defaultMessage="Content"
                      description="Confirmation Email Content label"
                    />
                  }
                >
                  <TinyMCEEditor
                    content={emailTemplate.translations[langCode].content}
                    onEditorChange={(newValue, editor) =>
                      onChange({
                        target: {
                          name: `form.confirmationEmailTemplate.translations.${langCode}.content`,
                          value: newValue,
                        },
                      })
                    }
                  />
                </Field>
              </FormRow>
              <FormRow>
                <Field
                  name="form.confirmationEmailOption"
                  label={
                    <FormattedMessage
                      defaultMessage="Email option"
                      description="Form confirmation email label"
                    />
                  }
                  helpText={
                    <FormattedMessage
                      defaultMessage="Will send the email specified."
                      description="Form confirmation email help text"
                    />
                  }
                  disabled={langCode !== defaultLang}
                >
                  <Select
                    name="form.confirmationEmailOption"
                    choices={emailOptions}
                    value={emailOption}
                    onChange={onChange}
                  />
                </Field>
              </FormRow>
            </>
          )}
        </LanguageTabs>
      </Fieldset>
    </div>
  );
};

Confirmation.propTypes = {
  displayMainPage: PropTypes.bool,
  emailOption: PropTypes.string,
  emailTemplate: PropTypes.object,
  includeConfirmationPageContentInPdf: PropTypes.bool,
  onChange: PropTypes.func.isRequired,
  translations: PropTypes.objectOf(
    PropTypes.shape({
      submissionConfirmationTemplate: PropTypes.string,
    })
  ),
};

export default Confirmation;
