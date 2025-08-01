(function () {
  'use strict';

  const toggle = document.querySelector('#navigation-toggle');
  const menu = document.querySelector('#navigation');

  toggle.addEventListener('click', function(){
    if (menu.classList.contains('is-active')) {
      this.setAttribute('aria-expanded', 'false');
      menu.classList.remove('is-active');
    } else {
      menu.classList.add('is-active'); 
      this.setAttribute('aria-expanded', 'true');
    }
  });
  
})();