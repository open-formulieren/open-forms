import PropTypes from 'prop-types';
import React from 'react';

/**
 * Render a list of messages of varying 'level'
 *
 * Usage:
 *
 *   <MessageList messages={messages} />
 *
 * or
 *
 *   <MessageList>{messages}</MessageList>
 *
 * The prop has higher prio than children.
 */
const MessageList = ({messages = [], children = []}) => {
  messages = messages.length ? messages : children;
  if (!messages.length) return null;
  return (
    <ul className="messagelist">
      {messages.map((item, index) => {
        return (
          <li key={index} className={item.level}>
            {item.message}
          </li>
        );
      })}
    </ul>
  );
};

const MessageListType = PropTypes.arrayOf(
  PropTypes.shape({
    level: PropTypes.string.isRequired,
    message: PropTypes.node.isRequired,
  })
);

MessageList.propTypes = {
  messages: MessageListType,
  children: MessageListType,
};

export default MessageList;
