const TEMPLATE = `
<div ref="partners">
  <label for="email">{{ ctx.t('Email') }}</label>
  <input type="email" name="email" id="email" class="form-control"/>

  <label for="phoneNumber">{{ ctx.t('Phone number') }}</label>
  <input type="tel" name="phoneNumber" id="phoneNumber" class="form-control"/>
</div>
`;

export default TEMPLATE;
