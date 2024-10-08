import {Formik} from 'formik';
import PropTypes from 'prop-types';

import {SubmitAction} from 'components/admin/forms/ActionButton';
import SubmitRow from 'components/admin/forms/SubmitRow';

import DefaultFields from './DefaultFields';
import ObjectsAPIFields from './ObjectsAPIFields';

const PLUGIN_COMPONENT_MAPPING = {
  objects_api: ObjectsAPIFields,
  default: DefaultFields,
};

const PrefillConfigurationForm = ({
  onSubmit,
  plugin = '',
  attribute = '',
  identifierRole = 'main',
  // TODO: find a better way to specify this based on the selected plugin
  options = {
    objectsApiGroup: '',
    objecttype: '',
    objecttypeVersion: null,
    variablesMapping: [],
  },
  errors,
}) => {
  return (
    <Formik
      initialValues={{
        plugin,
        attribute,
        identifierRole,
        options,
      }}
      onSubmit={(values, actions) => {
        // TODO should be implemented in https://github.com/open-formulieren/open-forms/issues/4693
        console.log(values);
        onSubmit(values);
        actions.setSubmitting(false);
      }}
    >
      {({handleSubmit, values}) => {
        const PluginFormComponent =
          PLUGIN_COMPONENT_MAPPING[values.plugin] ?? PLUGIN_COMPONENT_MAPPING.default;
        return (
          <>
            <PluginFormComponent errors={errors} />

            <SubmitRow>
              <SubmitAction
                onClick={event => {
                  event.preventDefault();
                  handleSubmit(event);
                }}
              />
            </SubmitRow>
          </>
        );
      }}
    </Formik>
  );
};

PrefillConfigurationForm.propTypes = {
  onSubmit: PropTypes.func.isRequired,
  plugin: PropTypes.string,
  attribute: PropTypes.string,
  identifierRole: PropTypes.string,
  errors: PropTypes.shape({
    plugin: PropTypes.arrayOf(PropTypes.string),
    attribute: PropTypes.arrayOf(PropTypes.string),
    identifierRole: PropTypes.arrayOf(PropTypes.string),
  }).isRequired,
};

export default PrefillConfigurationForm;
