const TEMPLATE = `
<div ref="customerProfile">
  {%
    ctx.component.digitalAddressTypes
      .sort((a, b) => a.localeCompare(b))
      .forEach(function(addressType) {
  %}
    <label for="{{addressType}}">
      {% if (addressType === "email") { %}
        {{ ctx.t('Email') }}
      {% } else if (addressType === "phoneNumber") { %}
        {{ ctx.t('Phone number') }}
      {% } else { %}
        {{ ctx.t(addressType) }}
      {% } %}
    </label>
    <input type="text" name="{{addressType}}" id="{{addressType}}" class="form-control"/>
  {% }) %}
</div>
`;

export default TEMPLATE;
