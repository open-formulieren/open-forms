import {Formio,} from 'formiojs';
import {defineChoicesEditFormTabs, defineInputInfo} from './abstract';


defineChoicesEditFormTabs(Formio.Components.components.select, 'data.values');

export const getTemplate = () => {
    defineInputInfo(Formio.Components.components.select, 'select');

    return `
        <select
          ref="{{ctx.input.ref ? ctx.input.ref : 'selectContainer'}}"
          {{ ctx.input.multiple ? 'multiple' : '' }}
          
          {% for (var attr in ctx.input.attr) { %}
            {{attr}}="{{ctx.input.attr[attr]}}"
          {% } %}
          
          {% if (!ctx.input.attr.id) { %}
            id="{{ctx.instance.id}}-{{ctx.component.key}}"
          {% } %}
        >
            {{ctx.selectOptions}}
    </select>
    `;
};
