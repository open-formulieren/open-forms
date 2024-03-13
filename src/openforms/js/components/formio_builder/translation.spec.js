import {extractComponentLiterals} from './translation';

describe('Checking date/datetime translation literals', () => {
  it('removes placeholder translation from date and datetime', () => {
    const dateComponent = {
      type: 'date',
      key: 'date',
      label: 'Date',
      description: '',
      placeholder: 'dd-mm-yyyy',
      tooltip: '',
      format: 'dd-MM-yyyy',
    };

    const dateTimeComponent = {
      type: 'datetime',
      key: 'dateTime',
      label: 'Date / Time',
      description: '',
      placeholder: 'dd-MM-yyyy HH:mm',
      tooltip: '',
      format: 'dd-MM-yyyy HH:mm',
    };

    expect(extractComponentLiterals(dateComponent)[0].literal).toStrictEqual('Date');
    expect(extractComponentLiterals(dateTimeComponent)[0].literal).toStrictEqual('Date / Time');
  });
});
