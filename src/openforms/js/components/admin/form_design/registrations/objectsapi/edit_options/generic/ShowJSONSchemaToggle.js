import isEqual from 'lodash/isEqual';
import {FormattedMessage} from 'react-intl';
import {useToggle} from 'react-use';

const SchemaDisplay = ({availablePaths, targetPath}) => {
  const needle = availablePaths.find(t => isEqual(t.targetPath, targetPath));
  return JSON.stringify(needle.jsonSchema, null, 2);
};

/**
 * Render a container with a toggle link to display the JSON Schema of the selected
 * property path.
 */
const ShowJSONSchemaToggle = ({availablePaths = [], targetPath = []}) => {
  const [jsonSchemaVisible, toggleJsonSchemaVisible] = useToggle(false);
  return (
    <div style={{marginTop: '1em'}}>
      <a
        href="#"
        onClick={e => {
          e.preventDefault();
          toggleJsonSchemaVisible();
        }}
      >
        <FormattedMessage
          description="Objects API variable configuration editor JSON Schema visibility toggle"
          defaultMessage="Toggle JSON Schema"
        />
      </a>
      {jsonSchemaVisible && (
        <pre style={{marginTop: '1em'}}>
          {!availablePaths.length || !targetPath.length ? (
            <FormattedMessage description="Not applicable" defaultMessage="N/A" />
          ) : (
            <SchemaDisplay availablePaths={availablePaths} targetPath={targetPath} />
          )}
        </pre>
      )}
    </div>
  );
};

export default ShowJSONSchemaToggle;
