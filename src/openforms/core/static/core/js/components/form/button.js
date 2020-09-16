import {Formio} from 'formiojs';
import {defineInputInfo} from './abstract';


defineInputInfo(Formio.Components.components.button, 'button', 'button', '', 'component.label');


export const button = `
<{{ctx.input.type}}
  ref="button"
  {% for (var attr in ctx.input.attr) { %}
  {{attr}}="{{ctx.input.attr[attr]}}"
  {% } %}
>
    {% if (ctx.component.leftIcon) { %}
        <span class="{{ctx.component.leftIcon}}"></span>&nbsp;
    {% } %}
    
    {{ctx.input.content}}
    
    {% if (ctx.component.tooltip) { %}
        <i ref="tooltip" class="{{ctx.iconClass('question-sign')}} text-muted"></i>
    {% } %}
    
    {% if (ctx.component.rightIcon) { %}
        &nbsp;<span class="{{ctx.component.rightIcon}}"></span>
    {% } %}
</{{ctx.input.type}}>

<div ref="buttonMessageContainer">
    <span class="help-block" ref="buttonMessage"></span>
</div>
`;
