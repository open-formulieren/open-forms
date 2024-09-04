import PropTypes from 'prop-types';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import Fieldset from 'components/admin/forms/Fieldset';
import FormRow from 'components/admin/forms/FormRow';
import {TextInput} from 'components/admin/forms/Inputs';

import TinyMCEEditor from './Editor';
import LanguageTabs from './LanguageTabs';
import {slugify} from './utils';

/**
 * Component to render the metadata admin form for an Open Forms form.
 */
const FormDetailFields = ({form: {slug, translations, appointmentOptions}, onChange}) => {
  const {isAppointment = false} = appointmentOptions;
  const setFormSlug = event => {
    // do nothing if there's already a slug set
    if (slug) return;

    // sort-of taken from Django's jquery prepopulate module
    const newSlug = slugify(event.target.value);
    onChange({
      target: {
        name: 'form.slug',
        value: newSlug,
      },
    });
  };

  return (
    <Fieldset
      title={
        <FormattedMessage defaultMessage="Form details" description="Form details fieldset title" />
      }
    >
      <LanguageTabs forceRenderTabPanel>
        {langCode => (
          <>
            <FormRow>
              <Field
                name={`form.translations.${langCode}.name`}
                label={
                  <FormattedMessage defaultMessage="Name" description="Form name field label" />
                }
                helpText={
                  <FormattedMessage
                    defaultMessage="Name/title of the form"
                    description="Form name field help text"
                  />
                }
                required
              >
                <TextInput
                  value={translations[langCode].name}
                  onChange={onChange}
                  onBlur={setFormSlug}
                  maxLength="150"
                />
              </Field>
            </FormRow>

            {!isAppointment && (
              <>
                <FormRow>
                  <Field
                    name={`form.translations.${langCode}.introductionPageContent`}
                    label={
                      <FormattedMessage
                        description="form.introductionPageContent label"
                        defaultMessage="Introduction page"
                      />
                    }
                    helpText={
                      <FormattedMessage
                        description="form.introductionPageContent help text"
                        defaultMessage={`Content for the introduction page that leads to the start page of the
                          form. Leave blank to disable the introduction page.`}
                      />
                    }
                  >
                    <TinyMCEEditor
                      content={translations[langCode].introductionPageContent}
                      onEditorChange={(newValue, editor) =>
                        onChange({
                          target: {
                            name: `form.translations.${langCode}.introductionPageContent`,
                            value: newValue,
                          },
                        })
                      }
                    />
                  </Field>
                </FormRow>

                <FormRow>
                  <Field
                    name={`form.translations.${langCode}.explanationTemplate`}
                    label={
                      <FormattedMessage
                        defaultMessage="Explanation template"
                        description="Start page explanation text label"
                      />
                    }
                    helpText={
                      <FormattedMessage
                        defaultMessage="Content that will be shown on the start page of the form, below the title and above the log in text."
                        description="Start page explanation text"
                      />
                    }
                  >
                    <TinyMCEEditor
                      content={translations[langCode].explanationTemplate}
                      onEditorChange={(newValue, editor) =>
                        onChange({
                          target: {
                            name: `form.translations.${langCode}.explanationTemplate`,
                            value: newValue,
                          },
                        })
                      }
                    />
                  </Field>
                </FormRow>
              </>
            )}
          </>
        )}
      </LanguageTabs>
    </Fieldset>
  );
};

FormDetailFields.propTypes = {
  form: PropTypes.shape({
    slug: PropTypes.string.isRequired,
    translations: PropTypes.objectOf(
      PropTypes.shape({
        name: PropTypes.string.isRequired,
        explanationTemplate: PropTypes.string.isRequired,
      })
    ).isRequired,
  }).isRequired,
  onChange: PropTypes.func.isRequired,
};

export default FormDetailFields;
