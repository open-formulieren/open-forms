import {Formio} from 'formiojs';


/** @const {Class} */
const Base = Formio.Components.components.component;


/**
 * Determines the boolean value of a setting.
 *
 * @param value
 * @return {boolean}
 */
export function boolValue(value) {
    if (typeof value === 'boolean') {
        return value;
    } else if (typeof value === 'string') {
        return (value.toLowerCase() === 'true');
    } else {
        return !!value;
    }
}


Object.defineProperty(Base.prototype, 'className', {
        get: function () {
            let className = 'of-form-control ';
            className += `of-form-control--${this.component.type} `;

            if (this.key) {
                className += `of-form-control--${this.key} `;
            }
            if (this.component.multiple) {
                className += 'of-form-control--multiple ';
            }
            if (this.component.customClass) {
                className += this.component.customClass;
            }
            if (this.hasInput && this.component.validate && boolValue(this.component.validate.required)) {
                className += ' of-form-control--required';
            }
            if (this.labelIsHidden()) {
                className += ' of-form-control--label-hidden';
            }
            if (!this.visible) {
                className += ' of-form-control--hidden';
            }
            return className;
        }
    }
);


export const component = `
<div id="{{ctx.id}}" class="{{ctx.classes}}"{% if (ctx.styles) { %} styles="{{ctx.styles}}"{% } %} ref="component">
  {% if (ctx.visible) { %}
  {{ctx.children}}
  <div ref="messageContainer" class="of-errors"></div>
  {% } %}
</div>
`;
