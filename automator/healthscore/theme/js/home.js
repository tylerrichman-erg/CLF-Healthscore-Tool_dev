(function () {
  'use strict';

  // Scripts for home page form
  const form = document.getElementById("tract-form");
  const submitButton = document.getElementById('tract-form-submit');
  const addressField = document.getElementById('address');
  form.addEventListener('submit', function(){
    submitLoading() 
    return true;
  });

  window.addEventListener("pageshow", submitLoadingClear);

  function submitLoading() {
    if (addressField &&  addressField.value) {
      submitButton.classList.add('loading');
      submitButton.value = 'Loading...';
      submitButton.setAttribute('disabled','');
    }
  }

  function submitLoadingClear() {
    submitButton.classList.remove('loading');
    submitButton.value = 'Next';
    submitButton.removeAttribute('disabled','');
  }
  
})();