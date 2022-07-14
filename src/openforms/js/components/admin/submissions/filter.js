window.onload = function () {
  // Retrieve the filter link who displays only triggered rules
  triggeredLink = document.querySelector('.trigger-filter-list > .selected > a');

  // Retrieve the "All" corresponding string, depending the language
  all = document.querySelector('#trigger-filter-list__link--all').dataset.trigger;

  // Only triggered logs are displayed first
  document
    .querySelectorAll('.logic-table-body__trigger-' + triggeredLink.dataset.trigger)
    .forEach(trigger => {
      trigger.parentNode.classList.remove('logic-table-body__row--hidden');
    });
};

document.querySelectorAll('.trigger-filter-list__link').forEach(link => {
  link.addEventListener('click', event => {
    event.preventDefault();

    // Hiding all the rows first
    document.querySelectorAll('.logic-table-body__row').forEach(row => {
      row.classList.add('logic-table-body__row--hidden');
    });

    let triggered = event.target.dataset.trigger;

    // Change the focus of the selected filter
    document.querySelector('.selected').classList.remove('selected');
    event.target.parentNode.classList.add('selected');

    // Showing only rules corresponding to the selected trigger link
    if (triggered == all) {
      document.querySelectorAll('.logic-table-body__row').forEach(row => {
        row.classList.remove('logic-table-body__row--hidden');
      });
    } else {
      document.querySelectorAll('.logic-table-body__trigger-' + triggered).forEach(trigger => {
        trigger.parentNode.classList.remove('logic-table-body__row--hidden');
      });
    }
  });
});
