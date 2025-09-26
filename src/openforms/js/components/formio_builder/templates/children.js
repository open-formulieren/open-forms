const TEMPLATE = `
<div ref="children">

  <table class="table">
    <thead>
      <tr>
        {% if (ctx.component.enableSelection) { %}
          <th scope="col"></th>
        {% } %}
        <th scope="col">
          {{ ctx.t('BSN') }}
        </th>
        <th scope="col">
          {{ ctx.t('Firstnames') }}
        </th>
        <th scope="col">
          {{ ctx.t('Date of birth') }}
        </th>
      </tr>
    </thead>

    <tbody>
      <tr>
        {% if (ctx.component.enableSelection) { %}
          <th scope="row">
            <input type="checkbox">
          </th>
        {% } %}
        <td>XXXXXX123</td>
        <td>Alice</td>
        <td>2000-01-01</td>
      </tr>
      <tr>
        {% if (ctx.component.enableSelection) { %}
          <th scope="row">
            <input type="checkbox">
          </th>
        {% } %}
        <td>XXXXXX456</td>
        <td>Bob</td>
        <td>2003-10-16</td>
      </tr>
    </tbody>

  </table>
</div>
`;

export default TEMPLATE;
