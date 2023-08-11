import {Formio} from 'formiojs';

import {get} from 'utils/fetch';
import jsonScriptToVar from 'utils/json-script';

import {DEFAULT_VALUE} from './edit/options';
import {ADVANCED, SENSITIVE_BASIC, TRANSLATIONS, VALIDATION_BASIC} from './edit/tabs';
import {localiseSchema} from './i18n';

const BaseFileField = Formio.Components.components.file;

const getInformatieObjectTypen = (backend, options) => {
  switch (backend) {
    case 'zgw-create-zaak': {
      return get('/api/v2/registration/informatieobjecttypen', {
        zgw_api_group: options.zgwApiGroup,
        registration_backend: backend,
      });
    }
    case 'objects_api':
      return get('/api/v2/registration/informatieobjecttypen', {registration_backend: backend});
    default:
      return;
  }
};

const getSetOfBackends = instance => {
  const registrationInfo = instance?.options?.openForms?.registrationBackendInfoRef?.current;
  return registrationInfo || [];
};

const REGISTRATION = {
  key: 'registration',
  label: 'Registration',
  components: [
    {
      type: 'iotypeSelect',
      key: 'registration.informatieobjecttype',
      label: 'Informatieobjecttype',
      tooltip: 'Save the attachment in the Documents API with this InformatieObjectType.',
      dataSrc: 'custom',
      data: {
        custom(context) {
          const instance = context.instance;
          const backends = getSetOfBackends(instance);
          Promise.all(
            backends.map(({backend, options, key, name}) => {
              const backendLabel = name || key;
              return getInformatieObjectTypen(backend, options)?.then(response =>
                response.data?.length ? {backendLabel, data: response.data} : null
              );
            })
          ).then(labeledDataAndNulls => {
            // not all backends do a fetch, not all responses contain data
            const labeledData = labeledDataAndNulls.filter(Boolean);
            // no need for label if we have one backend
            if (backends.length == 1 && labeledData.length) labeledData[0].backendLabel = '';
            const labeledItems = labeledData
              .map(({backendLabel, data}) => data.map(item => ({backendLabel, item})))
              .reduce((joinedArray, items) => joinedArray.concat(items), []);
            instance.setItems(labeledItems);
          });
        },
      },
      valueProperty: 'url',
    },
    {
      type: 'textfield',
      key: 'registration.bronorganisatie',
      label: 'Bronorganisatie',
      tooltip: 'RSIN of the organization which creates the ENKELVOUDIGINFORMATIEOBJECT.',
    },
    {
      type: 'select',
      key: 'registration.docVertrouwelijkheidaanduiding',
      label: 'Vertrouwelijkheidaanduiding',
      widget: 'choicesjs',
      tableView: true,
      data: {
        get values() {
          return jsonScriptToVar('CONFIDENTIALITY_LEVELS');
        },
      },
      tooltip:
        'Indication of the level to which extent the INFORMATIEOBJECT is meant to be public.',
    },
    {
      type: 'textfield',
      key: 'registration.titel',
      label: 'Title',
      validate: {
        maxLength: 200,
      },
      tooltip: 'The name under which the INFORMATIEOBJECT is formally known.',
    },
  ],
};

const FILE_TAB = {
  key: 'file',
  label: 'File',
  components: [
    // note this is a subset with some additions of the standard formio file component tab
    {
      type: 'textfield',
      input: true,
      key: 'file.name',
      label: 'File Name Template',
      placeholder: '(optional)',
      tooltip:
        'Specify template for name of uploaded file(s). <code>{‍{ fileName }‍}</code> contains the original filename.',
      weight: 25,
    },
    {
      type: 'select',
      key: 'file.type',
      input: true,
      label: 'File types',
      widget: 'choicesjs',
      tableView: true,
      multiple: true,
      data: {
        get values() {
          return jsonScriptToVar('config-UPLOAD_FILETYPES');
        },
      },
      weight: 30,
    },
    {
      type: 'hidden',
      key: 'file.allowedTypesLabels',
      calculateValue(context) {
        const labelValueMap = jsonScriptToVar('config-UPLOAD_FILETYPES');
        if (!Array.isArray(context.data?.file?.type)) return '';

        return labelValueMap
          .filter(item => context.data.file.type.includes(item.value))
          .map(item => item.label);
      },
    },
    {
      type: 'checkbox',
      input: true,
      key: 'useConfigFiletypes',
      label: 'Use globally configured filetypes',
      tooltip:
        'When this is checked, the filetypes configured in the global settings will be used.',
      weight: 31,
    },
    {
      type: 'checkbox',
      input: true,
      key: 'of.image.resize.apply',
      label: 'Resize image',
      tooltip: 'When this is checked, the image will be resized.',
      weight: 33,
      customConditional:
        'show = data.file.type.some(function(v) { return (v.indexOf("image/") > -1) || (v == "*"); });',
    },
    {
      key: 'of.image.resize.columns',
      type: 'columns',
      input: false,
      tableView: false,
      label: 'Columns',
      columns: [
        {
          components: [
            {
              key: 'of.image.resize.width',
              type: 'number',
              label: 'Maximum width',
              mask: false,
              tableView: false,
              delimiter: false,
              requireDecimal: false,
              inputFormat: 'plain',
              truncateMultipleSpaces: false,
              input: true,
              defaultValue: 2000,
            },
          ],
          width: 6,
          offset: 0,
          push: 0,
          pull: 0,
          size: 'md',
          currentWidth: 6,
        },
        {
          components: [
            {
              key: 'of.image.resize.height',
              type: 'number',
              label: 'Maximum height',
              mask: false,
              tableView: false,
              delimiter: false,
              requireDecimal: false,
              inputFormat: 'plain',
              truncateMultipleSpaces: false,
              input: true,
              defaultValue: 2000,
            },
          ],
          width: 6,
          offset: 0,
          push: 0,
          pull: 0,
          size: 'md',
          currentWidth: 6,
        },
      ],
      conditional: {
        json: {'==': [{var: 'data.of.image.resize.apply'}, true]},
      },
    },
    // it would be nice for UIX if this would work
    // (enabling this show a thumbnail after upload and switches features the SDK (in formio and in our FileField.js override)
    // {
    //     // used by the formio widget
    //     type: 'hidden',
    //     input: false,
    //     key: 'image',
    //     label: 'Show as Image',
    //     weight: 33,
    //     // the logic here seems fine (same as for the resize option) but doesn't set the value as expected
    //     customConditional: 'value = data.file.type.some(function(v) { return (v.indexOf("image/") > -1) || (v == "*"); });',
    // },
    {
      // used by the formio widget
      type: 'hidden',
      input: false,
      key: 'filePattern',
      label: 'File Pattern',
      logic: [
        {
          name: 'filePatternTrigger',
          trigger: {
            type: 'javascript',
            javascript: 'result = true;',
          },
          actions: [
            {
              name: 'filePatternAction',
              type: 'customAction',
              customAction: 'value = data.file.type.join(",")',
            },
          ],
        },
      ],
      weight: 50,
    },
    {
      // used by the formio widget
      type: 'textfield',
      input: true,
      key: 'fileMaxSize',
      label: 'File Maximum Size',
      placeholder: '10MB',
      tooltip:
        "See <a href='https://github.com/danialfarid/ng-file-upload#full-reference' target='_blank'>https://github.com/danialfarid/ng-file-upload#full-reference</a> for how to specify file sizes.",
      weight: 70,
      description: 'Note that the server upload limit is {{serverUploadLimit}}.',
      validate: {
        pattern: '[a-zA-Z0-9\\s]*', // Bandaid to prevent users from using a file size with decimals (Issue #1398)
        customMessage: 'Please specify an integer file size (e.g. 50 MB)',
      },
    },
    {
      type: 'number',
      input: true,
      label: 'Maximum number of files',
      key: 'maxNumberOfFiles',
      tooltip: 'The maximum number of files that can be uploaded',
      validate: {
        min: 1,
      },
    },
    // {
    //     // used by the formio widget
    //     type: 'checkbox',
    //     input: true,
    //     key: 'webcam',
    //     label: 'Enable web camera',
    //     tooltip: 'This will allow using an attached camera to directly take a picture instead of uploading an existing file.',
    //     weight: 32,
    //     conditional: {
    //         // this is not correct, see the conditionals in image.resize (etc)
    //         json: {'==': [{var: 'data.file.type'}, 'image']}
    //     }
    // },
  ],
};

class FileField extends BaseFileField {
  static schema(...extend) {
    const schema = BaseFileField.schema(
      {
        type: 'file',
        label: 'File Upload',
        key: 'file',
        storage: 'url',
        url: '', // backend sets this
        options: '{"withCredentials": true}',
        webcam: false,
        input: true,
        fileMaxSize: '10MB', // override default of 1GB
      },
      ...extend
    );
    return localiseSchema(schema);
  }

  static get builderInfo() {
    return {
      title: 'File Upload',
      icon: 'file',
      group: 'basic',
      weight: 10,
      schema: FileField.schema(),
    };
  }

  get defaultSchema() {
    return FileField.schema();
  }

  static editForm() {
    return {
      components: [
        {
          type: 'tabs',
          key: 'tabs',
          components: [
            {
              ...SENSITIVE_BASIC,
              components: SENSITIVE_BASIC.components.filter(
                option => option.key !== DEFAULT_VALUE.key
              ),
            },
            ADVANCED,
            VALIDATION_BASIC,
            FILE_TAB,
            REGISTRATION,
            TRANSLATIONS,
          ],
        },
      ],
    };
  }
}

export default FileField;
