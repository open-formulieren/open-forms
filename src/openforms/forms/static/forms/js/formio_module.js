import TextField from './components/form/text';
import IbanField from './components/form/iban';
import DateField from './components/form/date';
import TimeField from './components/form/time';

const FormIOModule = {
  components: {
    textfield: TextField,
    iban: IbanField,
    date: DateField,
    time: TimeField,
  },
};

export default FormIOModule;
