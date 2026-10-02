const STATIC_URL = '/static/';

export interface BooleanIconProps {
  icon: 'yes' | 'no' | 'unknown';
}

const BooleanIcon: React.FC<BooleanIconProps & React.ComponentProps<'img'>> = ({
  icon,
  ...props
}) => {
  const fullUrl = `${STATIC_URL}admin/img/icon-${icon}.svg`;
  return <img src={fullUrl} {...props} />;
};

const IconYes: React.FC = () => <BooleanIcon icon="yes" alt="True" />;
const IconNo: React.FC = () => <BooleanIcon icon="no" alt="False" />;
const IconUnknown: React.FC = () => <BooleanIcon icon="unknown" alt="None" />;

export default BooleanIcon;
export {IconYes, IconNo, IconUnknown};
