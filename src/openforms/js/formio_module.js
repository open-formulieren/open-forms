import TextArea from './components/form/textarea';
import TextField from './components/form/textfield';
import IbanField from './components/form/iban';
import DateField from './components/form/date';
import TimeField from './components/form/time';
import SignatureField from './components/form/signature';
import PhoneNumberField from './components/form/phoneNumber';
import BsnField from './components/form/bsn';
import PostcodeField from "./components/form/postcode";
import FileField from "./components/form/file";

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
  },
};

export default FormIOModule;
