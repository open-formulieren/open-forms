import {Formio} from 'formiojs';
import {defineChoicesEditFormTabs, defineInputInfo} from './abstract';


defineChoicesEditFormTabs(Formio.Components.components.radio);
defineChoicesEditFormTabs(Formio.Components.components.selectboxes);


export const getTemplate = () => {
    defineInputInfo(Formio.Components.components.radio, 'checkbox__input');

    return `
        <div class="form-choices">
          {% ctx.values.forEach(function(item) { %}
            <div class="form-choices__choice">
                <div class="checkbox">
                      <{{ctx.input.type}}
                        ref="input"
                        
                        {% for (var attr in ctx.input.attr) { %}
                          {{attr}}="{{ctx.input.attr[attr]}}"
                        {% } %}
                        
                        value="{{item.value}}"
                        
                        {% if (ctx.value && (ctx.value === item.value || (typeof ctx.value === 'object' && ctx.value.hasOwnProperty(item.value) && ctx.value[item.value]))) { %}
                          checked=true
                        {% } %}
                        
                        {% if (item.disabled) { %}
                          disabled=true
                        {% } %}
                        
                        id="{{ctx.id}}{{ctx.row}}-{{item.value}}"
                      >
                        {{ctx.input.content}}
                    </{{ctx.input.type}}>
                    
                    <div class="checkbox__checkmark"></div>
                    
                    {% if (!ctx.component.optionsLabelPosition || ctx.component.optionsLabelPosition === 'right' || ctx.component.optionsLabelPosition === 'bottom') { %}
                        <label class="checkbox__label" for="{{ctx.id}}{{ctx.row}}-{{item.value}}">{{ctx.t(item.label)}}</label>
                    {% } %}
                </div>
            </div>
              {% }) %}
        </div>
    `;
}
