//
// Accessible Tooltip Component
// Adapted from https://inclusive-components.design/tooltips-tooltips/
//

(function() {
  // Get all the tooltip elements
  var tooltipTexts = document.querySelectorAll('.tooltip');

  // Iterate over them
  Array.prototype.forEach.call(tooltipTexts, function(tooltipText) {
    // Create the container element
    var container = document.createElement('span');
    container.setAttribute('class', 'tooltip-container');

    if (tooltipText.classList.contains('bottom')) {
      container.classList.add('bottom');
    }
    
    // Put it before the original element in the DOM
    tooltipText.parentNode.insertBefore(container, tooltipText);
    
    // Create the button element
    var tooltip = document.createElement('button');
    tooltip.setAttribute('type', 'button');
    tooltip.setAttribute('aria-label', 'more info');
    tooltip.setAttribute('data-tooltip-content', tooltipText.innerHTML);
    tooltip.textContent = '?';
    
    // Place the button element in the container
    container.appendChild(tooltip);
    
    // Create the live region
    var liveRegion = document.createElement('span');
    liveRegion.setAttribute('role', 'status');
    
    // Place the live region in the container
    container.appendChild(liveRegion);
    
    // Remove the original element
    tooltipText.parentNode.removeChild(tooltipText);
    
    // Build `data-tooltip-content` 
    var message = tooltip.getAttribute('data-tooltip-content');
    tooltip.setAttribute('data-tooltip-content', message);
    tooltip.removeAttribute('title');
    
    // Get the message from the data-content element
    message = tooltip.getAttribute('data-tooltip-content');

    // Get the live region element
    liveRegion = tooltip.nextElementSibling;

    // Store state of widget
    var messageActive = false;

    // Determine page offset
    // var offset = tooltip.getBoundingClientRect();
    // var viewportWidth = window.innerWidth;
    // var offsetDirection = '';
    // if ( offset.left > ( viewportWidth / 2 ) ) {
    //   offsetDirection = 'left';
    // } else {
    //   offsetDirection = 'right';
    // }

    // Toggle the message
    var toggleMessage = function (event) {
      // test if message is already open
      if (messageActive == false) {
        liveRegion.innerHTML = '';
        window.setTimeout(function() {
          liveRegion.innerHTML = '<span class="tooltip-bubble">'+ message +'</span>';
        }, 100);
      }
      messageActive = true;
    };
    
    // Close message
    var closeMessage = function (event) {
      liveRegion.innerHTML = '';
      messageActive = false;
    };

    // Close on outside click
    document.addEventListener('click', function (e) {
      if ( messageActive && (tooltip !== e.target)) {
        closeMessage();
      }                        
    });

    // Close on outside touch
    document.addEventListener('touchstart', function (e) {
      if ( messageActive && (tooltip !== e.target)) {
        closeMessage();
      }                        
    });

    // Remove tooltip on ESC
    tooltip.addEventListener('keydown', function(e) {
      if ((e.keyCode || e.which) === 27)
      closeMessage();
    });
    
    // Remove on blur
    tooltip.addEventListener('blur', function (e) {
      closeMessage();
    });

    // Remove on mouseout
    container.addEventListener('mouseleave', closeMessage);

    // Open on focus, mouseenter, and click
    tooltip.addEventListener('focus', toggleMessage);
    container.addEventListener('mouseenter', toggleMessage);
    tooltip.addEventListener('click', toggleMessage);
  });
}());