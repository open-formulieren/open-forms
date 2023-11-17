import {ChangelistColumn, ChangelistTable} from '.';

export default {
  title: 'Admin/Django/Tables',
  component: ChangelistTable,

  argTypes: {
    children: {
      table: {
        disable: true,
      },
    },
  },
};

export const FixedColumns = {
  render: ({data, linkProp, rowKey, linkColumn}) => (
    <ChangelistTable linkColumn={linkColumn} linkProp={linkProp} rowKey={rowKey} data={data}>
      <ChangelistColumn objProp="driver">
        <>Driver</>
      </ChangelistColumn>
      <ChangelistColumn objProp="team">
        <>Team</>
      </ChangelistColumn>
    </ChangelistTable>
  ),

  name: 'Fixed columns',

  argTypes: {
    rowKey: {
      table: {
        disable: true,
      },
    },

    linkColumn: {
      options: [0, 1],
      control: 'radio',
    },
  },

  args: {
    data: [
      {
        driver: 'VER',
        team: 'Red Bull',
        href: '#!/driver/VER',
      },
      {
        driver: 'HUL',
        team: 'Haas',
        href: '#!/driver/HUL',
      },
      {
        driver: 'SAI',
        team: 'Ferrari',
        href: '#!/driver/SAI',
      },
      {
        driver: 'SAR',
        team: 'Williams',
        href: '#!/driver/SAR',
      },
      {
        driver: 'HAM',
        team: 'Hamilton',
        href: '#!/driver/HAM',
      },
    ],

    rowKey: 'driver',
    linkColumn: 0,
    linkProp: 'href',
  },
};

export const NoLinkColumn = {
  render: ({data}) => (
    <ChangelistTable linkColumn={null} linkProp="href" rowKey="driver" data={data}>
      <ChangelistColumn objProp="driver">
        <>Driver</>
      </ChangelistColumn>
      <ChangelistColumn objProp="team">
        <>Team</>
      </ChangelistColumn>
    </ChangelistTable>
  ),

  name: 'No link column',

  argTypes: {
    rowKey: {
      table: {
        disable: true,
      },
    },

    linkColumn: {
      table: {
        disable: true,
      },
    },

    linkProp: {
      table: {
        disable: true,
      },
    },

    rowKey: {
      table: {
        disable: true,
      },
    },
  },

  args: {
    data: [
      {
        driver: 'VER',
        team: 'Red Bull',
        href: '#!/driver/VER',
      },
      {
        driver: 'HUL',
        team: 'Haas',
        href: '#!/driver/HUL',
      },
      {
        driver: 'SAI',
        team: 'Ferrari',
        href: '#!/driver/SAI',
      },
      {
        driver: 'SAR',
        team: 'Williams',
        href: '#!/driver/SAR',
      },
      {
        driver: 'HAM',
        team: 'Hamilton',
        href: '#!/driver/HAM',
      },
    ],
  },
};
