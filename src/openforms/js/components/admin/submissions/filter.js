window.onload = function () {
  // Retrieve the filter link who displays only triggered rules
  triggeredLink = document.querySelector('.trigger-filter-list > .selected > a');

  // Retrieve the "All" corresponding string, depending the language
  all = document.querySelector('.logic-rules-filter__link--all').dataset.trigger;

  // Only triggered logs are displayed first
  document
    .querySelectorAll('.logic-logs__col-body--trigger-' + triggeredLink.dataset.trigger)
    .forEach(trigger => {
      trigger.parentNode.classList.remove('logic-logs__row-body--hidden');
    });
};

document.querySelectorAll('.logic-rules-filter__link').forEach(link => {
  link.addEventListener('click', event => {
    event.preventDefault();

    // Hiding all the rows first
    document.querySelectorAll('.logic-logs__row-body').forEach(row => {
      row.classList.add('logic-logs__row-body--hidden');
    });

    let triggered = event.target.dataset.trigger;

    // Change the focus of the selected filter
    document.querySelector('.selected').classList.remove('selected');
    event.target.parentNode.classList.add('selected');

    // Showing only rules corresponding to the selected trigger link
    if (triggered == all) {
      document.querySelectorAll('.logic-logs__row-body').forEach(row => {
        row.classList.remove('logic-logs__row-body--hidden');
      });
    } else {
      document.querySelectorAll('.logic-logs__col-body--trigger-' + triggered).forEach(trigger => {
        trigger.parentNode.classList.remove('logic-logs__row-body--hidden');
      });
    }
  });
});
