const TEMPLATE = `
<div ref="children">
  <label for="bsn">{{ ctx.t('BSN') }}</label>
  <input type="text" name="bsn" id="bsn" disabled class="form-control"/>

  <label for="first-names">{{ ctx.t('Firstnames') }}</label>
  <input type="text" name="first-names" id="first-names" disabled class="form-control"/>

  <label for="date-of-birth">{{ ctx.t('Date of birth') }}</label>
  <input type="text" name="date-of-birth" id="date-of-birth" disabled class="form-control"/>
</div>
`;

export default TEMPLATE;
