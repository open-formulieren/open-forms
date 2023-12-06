import AddressNL from './components/form/addressNL';
import BsnField from './components/form/bsn';
import CheckboxField from './components/form/checkbox';
import CoSignFieldOld from './components/form/coSignOld';
import ColumnField from './components/form/columns';
import Component from './components/form/component';
import ContentField from './components/form/content';
import CoSignField from './components/form/cosign';
import CurrencyField from './components/form/currency';
import Datamap from './components/form/datamap';
import DateField from './components/form/date';
import DateTimeField from './components/form/datetime';
import EditGrid from './components/form/editGrid';
import EmailField from './components/form/email';
import FieldSet from './components/form/fieldset';
import FileField from './components/form/file';
import IbanField from './components/form/iban';
import InformatieObjectTypeSelectField from './components/form/iotype-select';
import LicensePlate from './components/form/licenseplate';
import Map from './components/form/map';
import NpFamilyMembers from './components/form/np-family-members';
import NumberField from './components/form/number';
import PasswordField from './components/form/password';
import PhoneNumberField from './components/form/phoneNumber';
import PostcodeField from './components/form/postcode';
import RadioField from './components/form/radio';
import SelectField from './components/form/select';
import SelectBoxesField from './components/form/selectBoxes';
import SignatureField from './components/form/signature';
import TextArea from './components/form/textarea';
import TextField from './components/form/textfield';
import TimeField from './components/form/time';
import WebformBuilder from './components/formio_builder/WebformBuilder';

const FormIOModule = {
  components: {
    component: Component,
    textarea: TextArea,
    textfield: TextField,
    checkbox: CheckboxField,
    iban: IbanField,
    date: DateField,
    datetime: DateTimeField,
    signature: SignatureField,
    time: TimeField,
    number: NumberField,
    phoneNumber: PhoneNumberField,
    bsn: BsnField,
    postcode: PostcodeField,
    file: FileField,
    select: SelectField,
    iotypeSelect: InformatieObjectTypeSelectField,
    radio: RadioField,
    selectboxes: SelectBoxesField,
    email: EmailField,
    map: Map,
    password: PasswordField,
    fieldset: FieldSet,
    licenseplate: LicensePlate,
    coSign: CoSignFieldOld,
    cosign: CoSignField,
    npFamilyMembers: NpFamilyMembers,
    columns: ColumnField,
    content: ContentField,
    currency: CurrencyField,
    editgrid: EditGrid,
    datamap: Datamap,
    addressNL: AddressNL,
  },
  builders: {
    webform: WebformBuilder,
  },
};

export default FormIOModule;
