import {Formio} from 'formiojs';
import {defineCommonEditFormTabs, defineInputInfo} from './abstract';

defineCommonEditFormTabs(Formio.Components.components.checkbox, [
    {
        input: true,
        key: 'defaultValue',
        label: 'Default Value',
        placeholder: 'Default Value',
        tooltip: 'This will be the value for this field before user interaction. Having a default value will override the placeholder text.',
        type: 'checkbox',
        weight: 5
    }
]);


export const getTemplate = () => {
    defineInputInfo(Formio.Components.components.checkbox, 'checkbox__input');

    return `
        <div class="checkbox">
            <{{ctx.input.type}}
              ref="input"
              {% for (var attr in ctx.input.attr) { %}
              {{attr}}="{{ctx.input.attr[attr]}}"
              {% } %}
              id="{{ctx.instance.id}}-{{ctx.component.key}}"
              {% if (ctx.checked) { %}checked=true{% } %}
            >

                {{ctx.input.content}}
            </{{ctx.input.type}}>

            <div class="checkbox__checkmark"></div>
            <label class="checkbox__label {{ctx.input.labelClass}}" for="{{ctx.instance.id}}-{{ctx.component.key}}">
                {{ctx.input.label}}&nbsp;
                {% if (ctx.component.tooltip) { %}
                    <i ref="tooltip" class="{{ctx.iconClass('question-sign')}}"></i>
                {% } %}

          </label>
        </div>
    `;
};
