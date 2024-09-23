import {useField} from 'formik';
import React from 'react';
import {FormattedMessage} from 'react-intl';

import TinyMCEEditor from 'components/admin/form_design/Editor';
import Field from 'components/admin/forms/Field';
import FormRow from 'components/admin/forms/FormRow';

const EmailContentTemplateHTML = () => {
  const [fieldProps, , fieldHelpers] = useField('emailContentTemplateHtml');
  const {setValue} = fieldHelpers;
  return (
    <FormRow>
      <Field
        name="emailContentTemplateHtml"
        label={
          <FormattedMessage
            description="Email registration options 'emailContentTemplateHtml' label"
            defaultMessage="Email content template HTML"
          />
        }
        helpText={
          <FormattedMessage
            description="Email registration options 'emailContentTemplateHtml' helpText"
            defaultMessage="Content of the registration email message (as html)."
          />
        }
      >
        <TinyMCEEditor
          content={fieldProps.value}
          onEditorChange={(newValue, editor) => setValue(newValue)}
        />
      </Field>
    </FormRow>
  );
};

EmailContentTemplateHTML.propTypes = {};

export default EmailContentTemplateHTML;
