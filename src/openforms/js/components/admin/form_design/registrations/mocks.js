import {rest} from 'msw';

import {API_BASE_URL} from 'utils/fetch';

export const mockInformatieobjecttypenGet = informatieobjecttypen =>
  rest.get(`${API_BASE_URL}/api/v2/registration/informatieobjecttypen`, (req, res, ctx) => {
    const catalogusDomein = req.url.searchParams.get('catalogus_domein');
    const catalogusRsin = req.url.searchParams.get('catalogus_rsin');
    let filteredIots;
    if (catalogusDomein && catalogusRsin) {
      filteredIots = informatieobjecttypen.filter(
        iot => iot.catalogus.domein === catalogusDomein && iot.catalogus.rsin === catalogusRsin
      );
    } else {
      filteredIots = informatieobjecttypen;
    }

    return res(ctx.json(filteredIots));
  });

export const mockCatalogiGet = catalogi =>
  rest.get(`${API_BASE_URL}/api/v2/registration/catalogi`, (req, res, ctx) => {
    return res(ctx.json(catalogi));
  });
