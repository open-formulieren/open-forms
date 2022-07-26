function init() {
  // Retrieve the filter link that displays only triggered rules
  const triggeredLink = document.querySelector('.logic-rules-filter > .selected > a');

  document.querySelectorAll('.logic-rules-filter__link').forEach(link => {
    link.addEventListener('click', event => {
      // Hiding all the rows first
      document.querySelectorAll('.logic-logs__row-body').forEach(row => {
        row.classList.add('logic-logs__row-body--hidden');
      });

      const filterValue = event.target.dataset.trigger;

      // Change the focus of the selected filter
      document.querySelector('.logic-rules-filter .selected').classList.remove('selected');
      event.target.parentNode.classList.add('selected');

      let rows;
      switch (filterValue) {
        case 'all': {
          rows = document.querySelectorAll('.logic-logs__row-body');
          break;
        }
        case 'yes': {
          rows = [...document.querySelectorAll('.logic-logs__col-body--trigger-yes')].map(
            row => row.parentNode
          );
          break;
        }
        case 'no': {
          rows = [...document.querySelectorAll('.logic-logs__col-body--trigger-no')].map(
            row => row.parentNode
          );
          break;
        }
      }
      for (const row of rows) {
        row.classList.remove('logic-logs__row-body--hidden');
      }
    });
  });

  // Simulates the click on the default selected link
  triggeredLink.click();
}

if (document.readyState !== 'loading') {
  init();
} else {
  document.addEventListener('DOMContentLoaded', init);
}
