import {Formio} from 'formiojs';
import {defineCommonEditFormTabs, defineInputInfo} from './abstract';


defineInputInfo(Formio.Components.components.textfield, 'input');
defineCommonEditFormTabs(Formio.Components.components.textfield);
defineInputInfo(Formio.Components.components.textarea, 'textarea', 'textarea');
defineCommonEditFormTabs(Formio.Components.components.textarea);

export const text = `
{% if (ctx.prefix || ctx.suffix) { %}
<div class="group">
{% } %}

{% if (ctx.prefix) { %}
<div class="prefix" ref="prefix">
    {% if(ctx.prefix instanceof HTMLElement){ %}
      {{ ctx.t(ctx.prefix.outerHTML) }}
    {% } else{ %}
      {{ ctx.t(ctx.prefix) }}
    {% } %}
</div>
{% } %}

<{{ctx.input.type}}
  ref="{{ctx.input.ref ? ctx.input.ref : 'input'}}"
  {% for (var attr in ctx.input.attr) { %}
  {{attr}}="{{ctx.input.attr[attr]}}"
  {% } %}
  id="{{ctx.instance.id}}-{{ctx.component.key}}"
>{{ctx.input.content}}</{{ctx.input.type}}>

{% if (ctx.component.showCharCount) { %}
<span class="charcount" ref="charcount"></span>
{% } %}

{% if (ctx.component.showWordCount) { %}
<span class="wordcount" ref="wordcount"></span>
{% } %}

{% if (ctx.suffix) { %}
<div class="suffix" ref="">
    {% if(ctx.suffix instanceof HTMLElement){ %}
      {{ ctx.t(ctx.suffix.outerHTML) }}
    {% } else{ %}
      {{ ctx.t(ctx.suffix) }}
    {% } %}
</div>
{% } %}

{% if (ctx.prefix || ctx.suffix) { %}
</div>
{% } %}
`;
