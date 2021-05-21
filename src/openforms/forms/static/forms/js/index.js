import { Formio } from 'react-formio';

import './components';
import OpenForms from './formio_module';

// use custom component overrides
Formio.use(OpenForms);
