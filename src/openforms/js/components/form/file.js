import {Formio} from 'formiojs';

import {get} from 'utils/fetch';

import {localiseSchema} from './i18n';

const BaseFileField = Formio.Components.components.file;

/**
 * Fetch the available informatieobjecttypen for a given registration backend.
 *
 * @param  {String} backend The registration backend identifier to query for.
 * @param  {Object} options The specified configuration options for the specified backend.
 * @return {Promise<{ok: boolean, status: number, data?: any} | null>}
 *         An async response data wrapper if the registration backend supports
 *         informatieobjecttypen, null otherwise.
 */
const getInformatieObjectTypen = async (backend, options) => {
  switch (backend) {
    case 'zgw-create-zaak': {
      return await get('/api/v2/registration/plugins/zgw-api/document-types', {
        zgw_api_group: options.zgwApiGroup,
      });
    }
    case 'objects_api':
      return await get('/api/v2/objects-api/document-types', {
        objects_api_group: options.objectsApiGroup,
      });
    default:
      return null;
  }
};

/**
 * Look up the possible backends that are configured for the entire form, managed in React state.
 *
 * @return {{backend: string; options: Object; key: string; name: string;}[]} An array of configured registration backends.
 */
const getSetOfBackends = instance => {
  const registrationInfo = instance?.options?.openForms?.registrationBackendInfoRef?.current;
  return registrationInfo || [];
};

/**
 * Fetch all the possible document types that can be configured from the backend.
 *
 * Each configured registration backend can offer its own document types that can be
 * used during registration. It is the responsibility of the form designer to select
 * document types from the appropriate backend if multiple backends are selected, or
 * registration may throw errors.
 *
 * @todo we can probably improve insight into the effect of registration backend vs.
 * logic here.
 *
 * @param  {WebformBuilder} webformBuilder
 * A (custom) Form.io web form builder instance, configured with additional options to
 * introspect the React state of the whole form designer.
 *
 * @return {Promise<{
 *   backendLabel: string;
 *   catalogueLabel: string;
 *   url: string;
 *   description: string;
 * }>[]}
 * An array of available documenttypes with the relevant backend label attached.
 */
export const getAvailableDocumentTypes = async webformBuilder => {
  const backends = getSetOfBackends(webformBuilder);

  // TODO: wrap in try/except since any promise could throw (due to network error or bugs)
  const labeledDataAndNulls = await Promise.all(
    backends.map(async ({backend, options, key, name}) => {
      const backendLabel = name || key;
      const response = await getInformatieObjectTypen(backend, options);
      if (!response) return null;
      if (!response.data?.length) return null;
      return {
        backendLabel,
        data: response.data,
      };
    })
  );

  // not all backends do a fetch, not all responses contain data
  const labeledData = labeledDataAndNulls.filter(Boolean);
  // no need for label if we have one backend
  if (backends.length == 1 && labeledData.length) labeledData[0].backendLabel = '';

  const labeledItems = labeledData
    .map(({backendLabel, data}) => data.map(item => ({backendLabel, ...item})))
    .reduce((joinedArray, items) => joinedArray.concat(items), []);

  return labeledItems;
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
}

export default FileField;
