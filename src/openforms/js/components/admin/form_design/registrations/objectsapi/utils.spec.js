import {EMPTY_VARIABLE} from 'components/admin/form_design/variables/constants';

import {asJsonSchema} from './utils';

test('JSON schema for single file upload component', () => {
  const component = {
    type: 'file',
    key: 'file',
    label: 'File',
    multiple: false,
  };
  const variable = {
    ...EMPTY_VARIABLE,
    source: 'component',
    key: 'file',
    dataType: 'array',
  };

  const schema = asJsonSchema(variable, {[component.key]: component});

  expect(schema).toEqual({
    type: 'string',
    format: 'uri',
  });
});

test('JSON schema for multiple file uploads component', () => {
  const component = {
    type: 'file',
    key: 'file',
    label: 'File',
    multiple: true,
  };
  const variable = {
    ...EMPTY_VARIABLE,
    source: 'component',
    key: 'file',
    dataType: 'array',
  };

  const schema = asJsonSchema(variable, {[component.key]: component});

  expect(schema).toEqual({
    type: 'array',
    items: {
      type: 'string',
      format: 'uri',
    },
  });
});

test('JSON schema for map components', () => {
  const component = {
    type: 'map',
    key: 'map',
    label: 'Point coordinates',
  };
  const variable = {
    ...EMPTY_VARIABLE,
    source: 'component',
    key: 'map',
    dataType: 'array',
  };

  const schema = asJsonSchema(variable, {[component.key]: component});

  // we could be stricter, but we basically expect GeoJSON at the other end, which is
  // quite complex.
  expect(schema).toEqual({
    type: 'object',
    properties: {
      type: {
        type: 'string',
      },
    },
  });
});
