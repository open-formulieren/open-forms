const TEMPLATE = `
<div ref="partners">
  <label for="bsn">BSN:</label>
  <input type="text" name="bsn" id="bsn" disabled class="form-control"/>

  <label for="initials">Initials:</label>
  <input type="text" name="initials" id="initials" disabled class="form-control"/>

  <label for="affixes">Affixes:</label>
  <input type="text" name="affixes" id="affixes" disabled class="form-control"/>

  <label for="lastname">Lastname:</label>
  <input type="text" name="lastname" id="lastname" disabled class="form-control"/>

  <label for="date-of-birth">Date of birth:</label>
  <input type="text" name="date-of-birth" id="date-of-birth" disabled class="form-control"/>
</div>
`;

export default TEMPLATE;
