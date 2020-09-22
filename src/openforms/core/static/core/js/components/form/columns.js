export const columns = `
    <div class="form__row">
    {% ctx.component.columns.forEach(function(column, index) { %}
        <div class="form__column" ref="{{ctx.columnKey}}">
            {{ctx.columnComponents[index]}}
        </div>
    {% }) %}   
    </div>
`;
