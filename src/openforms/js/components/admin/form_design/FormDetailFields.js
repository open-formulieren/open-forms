/*
global URLify;
 */
import React from 'react';
import PropTypes from 'prop-types';
import {FormattedMessage, useIntl} from 'react-intl';

import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';
import Fieldset from 'components/admin/forms/Fieldset';
import {TextInput} from 'components/admin/forms/Inputs';

import TinyMCEEditor from './Editor';

/**
 * Component to render the metadata admin form for an Open Forms form.
 */
const FormDetailFields = ({
  form,
  onChange,
  availableAuthPlugins,
  selectedAuthPlugins,
  onAuthPluginChange,
  availableCategories,
}) => {
  const {name, slug, explanationTemplate} = form;

  const intl = useIntl();

  const onCheckboxChange = (event, currentValue) => {
    const {
      target: {name},
    } = event;
    onChange({target: {name, value: !currentValue}});
  };

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
      <FormRow>
        <Field
          name="form.name"
          label={<FormattedMessage defaultMessage="Name" description="Form name field label" />}
          helpText={
            <FormattedMessage
              defaultMessage="Name/title of the form"
              description="Form name field help text"
            />
          }
          required
        >
          <TextInput value={name} onChange={onChange} onBlur={setFormSlug} maxLength="150" />
        </Field>
      </FormRow>

      <FormRow>
        <Field
          name="form.explanationTemplate"
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
            content={explanationTemplate}
            onEditorChange={(newValue, editor) =>
              onChange({target: {name: 'form.explanationTemplate', value: newValue}})
            }
          />
        </Field>
      </FormRow>
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
  availableAuthPlugins: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string,
      label: PropTypes.string,
      providesAuth: PropTypes.arrayOf(PropTypes.string),
    })
  ),
  selectedAuthPlugins: PropTypes.array.isRequired,
  onAuthPluginChange: PropTypes.func.isRequired,
};

export default FormDetailFields;
