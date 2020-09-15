import {Formio, Utils} from 'formiojs';


/** @const {Class} */
const Base = Formio.Components.components.textfield;

/** @const {string} */
const class_name = 'of-input';


Object.defineProperty(Base.prototype, 'inputInfo', {
        get: function () {
            const base = new Base();
            base.component = this.component;

            const info = base.elementInfo();
            info.attr.class = class_name;

            const result = {};
            Object.assign(result, this.component);
            Object.assign(result, info);
            return result;
        }
    }
);


Formio.Components.components.textfield.editForm = function () {
    return {
        components: [
            {
                type: 'tabs', key: 'tabs', components: [
                    {
                        key: 'basic',
                        label: 'Basic',
                        components: [
                            {
                                type: 'textfield', key: 'label', label: 'Label'
                            },
                            {
                                type: 'textfield', key: 'key', label: 'Property Name'
                            },
                            {
                                type: 'textfield', key: 'placeholder', label: 'Placeholder',
                                validate: {
                                    pattern: '(\\w|\\w[\\w-.]*\\w)',
                                    patternMessage: 'The property name must only contain alphanumeric characters, underscores, dots and dashes and should not be ended by dash or dot.'
                                }
                            },
                        ]
                    },
                    {
                        key: 'advanced',
                        label: 'Advanced',
                        components: [
                            {
                                type: 'panel',
                                title: 'Simple',
                                key: 'simple-conditional',
                                theme: 'default',
                                components: [
                                    {
                                        type: 'select',
                                        input: true,
                                        label: 'This component should Display:',
                                        key: 'conditional.show',
                                        dataSrc: 'values',
                                        data: {
                                            values: [
                                                {label: 'True', value: 'true'},
                                                {label: 'False', value: 'false'}
                                            ]
                                        }
                                    },
                                    {
                                        type: 'select',
                                        input: true,
                                        label: 'When the form component:',
                                        key: 'conditional.when',
                                        dataSrc: 'custom',
                                        valueProperty: 'value',
                                        data: {
                                            custom(context) {
                                                return Utils.getContextComponents(context);
                                            }
                                        }
                                    },
                                    {
                                        type: 'textfield',
                                        input: true,
                                        label: 'Has the value:',
                                        key: 'conditional.eq'
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    };
};


export const text = `
{% if (ctx.prefix || ctx.suffix) { %}
<div class="of-group">
{% } %}

{% if (ctx.prefix) { %}
<div class="of-supplementary" ref="prefix">
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
<span class="of-charcount" ref="charcount"></span>
{% } %}

{% if (ctx.component.showWordCount) { %}
<span class="of-wordcount" ref="wordcount"></span>
{% } %}

{% if (ctx.suffix) { %}
<div class="of-supplementary" ref="">
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
