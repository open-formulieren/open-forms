/*
global URLify;
 */
import React, {useContext} from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import Fieldset from 'components/admin/forms/Fieldset';
import {TextInput} from 'components/admin/forms/Inputs';

import {FormContext} from './Context';
import TinyMCEEditor from './Editor';
import LanguageTabs from './LanguageTabs';

/**
 * Component to render the metadata admin form for an Open Forms form.
 */
const FormDetailFields = ({form: {slug, translations}, onChange}) => {
  const {languages} = useContext(FormContext);

  const setFormSlug = event => {
    // do nothing if there's already a slug set
    if (slug) return;

    // sort-of taken from Django's jquery prepopulate module
    const newSlug = URLify(event.target.value, 100, false);
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
      </LanguageTabs>
    </Fieldset>
  );
};

FormDetailFields.propTypes = {
  form: PropTypes.shape({
    name: PropTypes.string.isRequired,
    uuid: PropTypes.string.isRequired,
    slug: PropTypes.string.isRequired,
    showProgressIndicator: PropTypes.bool.isRequired,
    active: PropTypes.bool.isRequired,
    isDeleted: PropTypes.bool.isRequired,
    maintenanceMode: PropTypes.bool.isRequired,
    translationEnabled: PropTypes.bool.isRequired,
    submissionConfirmationTemplate: PropTypes.string.isRequired,
    registrationBackend: PropTypes.string.isRequired,
    registrationBackendOptions: PropTypes.object,
  }).isRequired,
  onChange: PropTypes.func.isRequired,
};

export default FormDetailFields;
