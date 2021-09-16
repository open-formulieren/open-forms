import TextArea from './components/form/textarea';
import TextField from './components/form/textfield';
import IbanField from './components/form/iban';
import DateField from './components/form/date';
import TimeField from './components/form/time';
import SignatureField from './components/form/signature';
import PhoneNumberField from './components/form/phoneNumber';
import BsnField from './components/form/bsn';
import PostcodeField from './components/form/postcode';
import FileField from './components/form/file';
import SelectField from './components/form/select';
import RadioField from './components/form/radio';
import SelectBoxesField from './components/form/selectBoxes';

const FormIOModule = {
  components: {
    textarea: TextArea,
    textfield: TextField,
    iban: IbanField,
    date: DateField,
    signature: SignatureField,
    time: TimeField,
    phoneNumber: PhoneNumberField,
    bsn: BsnField,
    postcode: PostcodeField,
    file: FileField,
    select: SelectField,
    radio: RadioField,
    selectboxes: SelectBoxesField
  },
};

export default FormIOModule;
