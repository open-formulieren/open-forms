export const multipleMasksInput = `
<div class="group" ref="{{ctx.input.ref ? ctx.input.ref : 'input'}}">
  <select id="{{ctx.key}}-mask" ref="select"{% if (ctx.input.attr.disabled) { %}disabled{% } %}>
    {% ctx.selectOptions.forEach(function(option) { %}
        <option value="{{option.value}}">{{option.label}}</option>
    {% }); %}
  </select>
  
  <input ref="mask"
    {% for (var attr in ctx.input.attr) { %}
    {{attr}}="{{ctx.input.attr[attr]}}"
    {% } %}
  >
</div>
`;
