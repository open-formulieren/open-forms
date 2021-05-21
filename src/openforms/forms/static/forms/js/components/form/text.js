import {Formio} from 'react-formio';
import {defineCommonEditFormTabs, defineInputInfo} from './abstract';

class TextField extends Formio.Components.components.textfield {

}

defineCommonEditFormTabs(TextField);
defineCommonEditFormTabs(Formio.Components.components.textarea);


export default TextField;
