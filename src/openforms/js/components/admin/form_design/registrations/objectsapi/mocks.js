import {rest} from 'msw';

import {API_BASE_URL} from 'utils/fetch';

export const mockObjecttypesGet = objecttypes =>
  rest.get(
    `${API_BASE_URL}/api/v2/registration/plugins/objects-api/object-types`,
    (req, res, ctx) => {
      return res(ctx.json(objecttypes));
    }
  );

export const mockObjecttypeVersionsGet = versions =>
  rest.get(
    `${API_BASE_URL}/api/v2/registration/plugins/objects-api/object-types/:uuid/versions`,
    (req, res, ctx) => {
      return res(ctx.json(versions));
    }
  );

export const mockObjecttypesError = () =>
  rest.all('*', (req, res, ctx) => {
    return res(ctx.status(500));
  });

export const mockTargetPathsPost = paths =>
  rest.post(
    `${API_BASE_URL}/api/v2/registration/plugins/objects-api/target-paths`,
    async (req, res, ctx) => {
      const requestBody = await req.json();
      const variableJsonSchemaType = requestBody.variableJsonSchema.type;

      return res(ctx.json(paths[variableJsonSchemaType]));
    }
  );
