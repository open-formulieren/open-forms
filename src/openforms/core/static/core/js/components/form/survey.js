export const survey = `
<table class="table table--fixed">
  <thead class="">
    <tr class="table__row">
      <th class="table__head"></th>
      {% ctx.component.values.forEach(function(value) { %}
        <th class="table__head">
            <p class="body"><strong>{{ctx.t(value.label)}}</strong></p>
        </th>
      {% }) %}
    </tr>
  </thead>
  
  <tbody class="table__body">
    {% ctx.component.questions.forEach(function(question) { %}
        <tr class="table__row">
            <td class="table__cell">
                <p class="body">{{ctx.t(question.label)}}</p>
            </td>
      
          {% ctx.component.values.forEach(function(value) { %}
              <td class="table__cell">
                <input type="radio" name="{{ ctx.self.getInputName(question) }}" value="{{value.value}}" id="{{ctx.key}}-{{question.value}}-{{value.value}}" ref="input">
              </td>
          {% }) %}
          
        </tr>
    {% }) %}
  </tbody>
</table>
`;
