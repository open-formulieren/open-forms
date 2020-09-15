export const label = `
<label class="of-label {{ctx.label.className}}" for="{{ctx.instance.id}}-{{ctx.component.key}}">
  {{ ctx.t(ctx.component.label) }}
  {% if (ctx.component.tooltip) { %}
    <i ref="tooltip" class="{{ctx.iconClass('question-sign')}}"></i>
  {% } %}
</label>
`;
