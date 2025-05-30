document.addEventListener('DOMContentLoaded', function() {
    // Find all dropdown menus
    var dropdowns = document.querySelectorAll('.dropdown-menu');
    
    // For each dropdown menu
    dropdowns.forEach(function(dropdown) {
        // Prevent the dropdown from closing when you click on a checkbox
        dropdown.addEventListener('click', function(event) {
            event.stopPropagation();
        });
        
        // Find all the checkboxes in this dropdown
        var checkboxes = dropdown.querySelectorAll('input[type="checkbox"]');
        
        // For each checkbox
        checkboxes.forEach(function(checkbox) {
            // When the checkbox is clicked
            checkbox.addEventListener('change', function() {
                // Find the dropdown button
                var button = this.closest('.dropdown').querySelector('.dropdown-toggle');
                
                // Find all checked checkboxes
                var checked = dropdown.querySelectorAll('input[type="checkbox"]:checked');
                
                // Se houver checkboxes marcados
                if (checked.length > 0) {
                    // Create a list of selected values
                    var values = [];
                    checked.forEach(function(item) {
                        values.push(item.value);
                    });
                    
                    // Update the button text
                    button.textContent = values.join(', ');
                } else {
                    // If there are no selections, restore the default text
                    var name = checkbox.getAttribute('name');
                    
                    if (name === 'subjects') {
                        button.textContent = 'Select Subjects';
                    } else if (name === 'languages') {
                        button.textContent = 'Select Languages';
                    } else if (name === 'grade_levels') {
                        button.textContent = 'Select Grade Levels';
                    } else if (name === 'availability') {
                        button.textContent = 'Select Available Days';
                    }
                }
            });
        });
    });
});