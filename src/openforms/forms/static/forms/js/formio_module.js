import TextField from './components/form/text';
import IbanField from './components/form/iban';
import DateField from './components/form/date';
import TimeField from './components/form/time';
import SignatureField from './components/form/signature';
import PhoneNumberField from './components/form/phoneNumber';
import BsnField from './components/form/bsn';
import PostcodeField from "./components/form/postcode";

const FormIOModule = {
  components: {
    textfield: TextField,
    iban: IbanField,
    date: DateField,
    signature: SignatureField,
    time: TimeField,
    phoneNumber: PhoneNumberField,
    bsn: BsnField,
    postcode: PostcodeField,
  },
};

export default FormIOModule;
