const TEMPLATE = `
<table class="table datagrid-table table-bordered
    {{ ctx.component.striped ? 'table-striped' : ''}}
    {{ ctx.component.hover ? 'table-hover' : ''}}
    {{ ctx.component.condensed ? 'table-sm' : ''}}
    ">
  {% if (ctx.hasHeader) { %}
  <thead>
    <tr>
      {% ctx.columns.forEach(function(col) { %}
        <th class="{{col.validate && col.validate.required ? 'field-required' : ''}}">
          {{ col.hideLabel ? '' : ctx.t(col.label || col.title, { _userInput: true }) }}
          {% if (col.tooltip) { %} <i ref="tooltip" tabindex="0" data-title="{{col.tooltip}}" class="{{ctx.iconClass('question-sign')}} text-muted" data-tooltip="{{col.tooltip}}"></i>{% } %}
        </th>
      {% }) %}
    </tr>
  </thead>
  {% } %}
  <tbody>
    {% ctx.rows.forEach(function(row) { %}
    <tr>
      {% ctx.columns.forEach(function(col) { %}
        <td ref="{{ctx.datagridKey}}">
          {{row[col.key]}}
        </td>
      {% }) %}
    </tr>
    {% }) %}
  </tbody>
</table>
`;

export default TEMPLATE;
