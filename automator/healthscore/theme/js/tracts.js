(function () {
  'use strict';

  /**
   * Nunmber Inputs Cleanup
   */
  let numberInputs = document.querySelectorAll('input[inputmode="numeric"]');
  numberInputs.forEach((numberInput) => {
    numberInput.addEventListener('input', numberClean);
  });

  function numberClean(e) {
    let input = e.currentTarget;
    if(!isNaN(input.value.replace(/,/g, ""))) {
      input.value=input.value.replace(/,/g, "");
    }
  }

  /**
   * Delete Item Form Action
   */
  let formDeletes = document.querySelectorAll('.input-delete');
  formDeletes.forEach((formDelete) => {
    formDelete.addEventListener('click', deleteItem);
  });

  function deleteItem(e) {
    e.currentTarget.parentElement.remove();
  }

  /**
   * Add Item Form Action
   */
  let formAdds = document.querySelectorAll('.input-add');
  formAdds.forEach((formAdd) => {
    formAdd.addEventListener('click', addClonedItem);
  });

  function addClonedItem(e) {
    let element = e.currentTarget;
    let clone = element.parentElement.cloneNode(true);
    const buttonParent = element.parentElement;
    // Insert after
    buttonParent.parentNode.insertBefore(clone, buttonParent.nextSibling);
    // Add event listener to new button
    let newFormAdd = clone.querySelectorAll('.input-add');
    newFormAdd.forEach((formAdd) => {
      formAdd.addEventListener('click', addClonedItem)
    });
    // Clear out cloned input
    let newInputs = clone.querySelectorAll('input');
    newInputs.forEach((newInput) => {
      newInput.value = "";
    });
    // Switch previous button to delete row
    element.classList.remove('input-add');
    element.classList.add('input-delete');
    element.innerHTML = 'Delete';
    element.removeEventListener('click', addClonedItem);
    element.addEventListener('click', deleteItem);
  }

  /**
   * Add Form Row Action
   */
  let formAddRows = document.querySelectorAll('.button--add');
  formAddRows.forEach((formAddRow) => {
    formAddRow.addEventListener('click', addClonedRow);
  });

  function addClonedRow(e) {
    let element = e.currentTarget;
    let cloneClass = element.dataset.row;
    let rows = [];
    if (cloneClass) {
      rows = document.querySelectorAll('.' + cloneClass);
    }
    if (rows.length > 0) {
      let last = rows[rows.length - 1];
      const rowsParent = last.parentNode;
      let clone = last.cloneNode(true);
      // Insert after
      rowsParent.insertBefore(clone, last.nextSibling);
      // Clear out cloned input
      let newInputs = clone.querySelectorAll('input');
      newInputs.forEach((newInput) => {
        newInput.value = "";
      });
      // Add event listener to new button
      let newFormDelete = clone.querySelectorAll('.input-delete');
      newFormDelete.forEach((formDelete) => {
        formDelete.addEventListener('click',(e) => {    
          deleteItem(e);
          caclulateAffordability();    
        });
      });
      // Add event listener to number values
      let numberInputs = clone.querySelectorAll('input[inputmode="numeric"]');
      numberInputs.forEach((numberInput) => {
        numberInput.addEventListener('input', numberClean);
        numberInput.addEventListener('change', caclulateAffordability);
      });
    }
  }

  /**
   * Affordability Calculations
   */
  let affordability_inputs = document.querySelectorAll('.affordability-input-group input[inputmode="numeric"]');
  affordability_inputs.forEach((affordability_input) => {
    affordability_input.addEventListener('change', caclulateAffordability);
  });

  window.addEventListener("load", caclulateAffordability);

  function caclulateAffordability() {
    // Inputs
    let rows = document.querySelectorAll('.affordability-input-group');
    let unit_counts = document.querySelectorAll('input[name="housing_unit_count"]');
    let unit_percents = document.querySelectorAll('input[name="housing_unit_percent"]');
    let unit_rents = document.querySelectorAll('input[name="housing_rent"]');

    // Calculated Values
    let affordability_income_needed = document.getElementById('affordability-income-needed');
    let affordability_total_units = document.getElementById('affordability-total-units');
    let affordability_weighted_rent = document.getElementById('affordability-weighted-rent');

    // Calculate Total Units
    let total_units = 0;
    unit_counts.forEach((unit_counts) => {
      let count = unit_counts.value ? parseInt(unit_counts.value) : 0;
      total_units += count;
    });
    affordability_total_units.textContent = total_units.toString();

    // Calculate % of Total
    for (var i = 0; i < rows.length; i++) {
      if (rows.length == 1) {
        unit_percents[i].value = '100%';
      } else {
        let unit_count = unit_counts[i].value ? parseInt(unit_counts[i].value) : 0;
        let row_percent = parseInt((unit_count / total_units) * 100);
        unit_percents[i].value = row_percent + '%';
      }
    }

    // Calculate Weighted Average Rent Cost
    let weighted_rent = 0;
    for (var i = 0; i < rows.length; i++) {
      let rent = unit_rents[i].value ?  parseInt(unit_rents[i].value) : 0;
      if (rows.length == 1) {
        weighted_rent = rent;
      } else {
        let unit_count = unit_counts[i].value ? parseInt(unit_counts[i].value) : 0;
        let row_percent = parseFloat(unit_count / total_units);
        weighted_rent += row_percent * rent;
      }
    }
    weighted_rent = parseFloat(weighted_rent);
    affordability_weighted_rent.textContent = '$' + weighted_rent.toLocaleString("en-US", {minimumFractionDigits: 2, maximumFractionDigits: 2});

    // Calculate Annual Income Needed
    // Weighted Average Rent as 30% of Income times 12 months
    let income_needed = parseFloat(weighted_rent * 12 / 0.3).toLocaleString("en-US", {minimumFractionDigits: 2, maximumFractionDigits: 2});
    affordability_income_needed.textContent = '$' + income_needed;
  }

})();