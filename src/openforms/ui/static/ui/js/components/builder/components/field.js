export const field = `
{% if (!ctx.label.hidden && ctx.label.labelPosition !== 'bottom') { %}
  {{ ctx.labelMarkup }}
{% } %}

{% if (ctx.label.hidden && ctx.label.className && ctx.component.validate.required) { %}
  <label class="of-label {{ctx.label.className}}"></label>
{% } %}

{{ctx.element}}

{% if (!ctx.label.hidden && ctx.label.labelPosition === 'bottom') { %}
  {{ ctx.labelMarkup }}
{% } %}

{% if (ctx.component.description) { %}
  <div class="of-help-text">{{ctx.t(ctx.component.description)}}</div>
{% } %}
`;
