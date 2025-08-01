(function ($) {
  'use strict';

  //
  // Scripts for the My Scorecards page
  //

  // Add loading animation to edit buttons
  const editButtons = document.querySelectorAll(".button--edit");

  editButtons.forEach((editButton) => {
    editButton.addEventListener('click', function () {
      editButton.classList.add('loading');
      editButton.textContent = 'Loading...';
      editButton.setAttribute('disabled', '');
    })
  });

  // Allow title to be edited via ajax call
  let scorecards = document.querySelectorAll('.scorecard__title');
  scorecards.forEach((scorecard, index) => {
    let titleWrapper = scorecard.querySelector('span');
    let form = scorecard.parentElement.querySelector('form');
    let submitButton = form.querySelector('.form-submit');
    let cancelButton = form.querySelector('.form-cancel');
    let ajaxRequest = null;

    let titleEditButton = document.createElement('button');
    titleEditButton.setAttribute('type', 'button');
    titleEditButton.textContent = 'Edit title';
    titleEditButton.classList.add('button-link');

    titleEditButton.addEventListener('click', function () {
      form.classList.remove('is-hidden');
      scorecard.classList.add('is-hidden');
    });

    cancelButton.addEventListener('click', function () {
      form.classList.add('is-hidden');
      scorecard.classList.remove('is-hidden');
      if (ajaxRequest) {
        ajaxRequest.abort();
        submitButton.classList.remove('loading');
        submitButton.removeAttribute('disabled', '');
      }
    });

    submitButton.addEventListener('click', function (e) {
      e.preventDefault();
      submitButton.classList.add('loading');
      submitButton.setAttribute('disabled', '');
      let newTitleText = form.querySelector('input[name="title"]').value;
      let payload = $(form).serialize();

      ajaxRequest = $.ajax({
        url: "/save_title", // the endpoint
        type: "POST", // http method
        data: payload,

        // handle a successful response
        success: function (response) {
          submitButton.classList.remove('loading');
          submitButton.removeAttribute('disabled', '');
          titleWrapper.innerText = newTitleText;
          form.classList.add('is-hidden');
          scorecard.classList.remove('is-hidden');
        },

        // handle a non-successful response
        error: function (xhr, errmsg, err) {
          alert("Save failed. Please check logs.");
          submitButton.classList.remove('loading');
          submitButton.removeAttribute('disabled', '');
        }
      });
    });

    // Place the button element in the title
    scorecard.appendChild(titleEditButton);

  });


})(jQuery);