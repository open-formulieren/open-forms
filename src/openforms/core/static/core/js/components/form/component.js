import {Formio} from 'formiojs';


/** @const {Class} */
const Base = Formio.Components.components.component;

/** @const {string} */
const class_name = 'form-control';


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
            let className = 'form-control ';
            className += `form-control--${this.component.type} `;

            if (this.key) {
                className += `form-control--${this.key} `;
            }
            if (this.component.multiple) {
                className += 'form-control--multiple ';
            }
            if (this.component.customClass) {
                className += this.component.customClass;
            }
            if (this.hasInput && this.component.validate && boolValue(this.component.validate.required)) {
                className += ' form-control--required';
            }
            if (this.labelIsHidden()) {
                className += ' form-control--label-hidden';
            }
            if (!this.visible) {
                className += ' form-control--hidden';
            }
            return className;
        }
    }
);


export const component = `
<div id="{{ctx.id}}" class="{{ctx.classes}}"{% if (ctx.styles) { %} styles="{{ctx.styles}}"{% } %} ref="component">
  <div ref="messageContainer" class="errors"></div>
  {% if (ctx.visible) { %}
  {{ctx.children}}
  {% } %}
</div>
`;
