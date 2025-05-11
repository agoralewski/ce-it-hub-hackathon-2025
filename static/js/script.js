/* Main JavaScript file for KSP (Krwinkowy System Prezentowy) */

// Initialize select2 elements on page load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Select2 elements
    if (jQuery && jQuery.fn.select2) {
        $('.select2').select2({
            theme: 'bootstrap-5'
        });
    }
    
    // Initialize category autocomplete
    $('.category-select').select2({
        theme: 'bootstrap-5',
        placeholder: 'Wybierz kategorię',
        allowClear: true,
        ajax: {
            url: '/warehouse/api/autocomplete/categories/',
            dataType: 'json',
            delay: 250,
            processResults: function (data) {
                return {
                    results: data.results
                };
            },
            cache: true
        }
    });
    
    // Initialize item name autocomplete
    $('.item-autocomplete').autocomplete({
        source: function(request, response) {
            $.ajax({
                url: '/warehouse/api/autocomplete/items/',
                dataType: 'json',
                data: { term: request.term },
                success: function(data) {
                    // Map the results to the format jQuery UI autocomplete expects
                    response($.map(data.results, function(item) {
                        return {
                            label: item.text,
                            value: item.text
                        };
                    }));
                }
            });
        },
        minLength: 1,
        delay: 250,
        autoFocus: true,
        classes: {
            "ui-autocomplete": "dropdown-menu"
        }
    }).autocomplete("instance")._renderItem = function(ul, item) {
        // Custom rendering for Bootstrap styling
        return $("<li>")
            .append("<div class='dropdown-item'>" + item.label + "</div>")
            .appendTo(ul);
    };
    
    // Initialize manufacturer autocomplete
    $('.manufacturer-autocomplete').autocomplete({
        source: function(request, response) {
            $.ajax({
                url: '/warehouse/api/autocomplete/manufacturers/',
                dataType: 'json',
                data: { term: request.term },
                success: function(data) {
                    // Map the results to the format jQuery UI autocomplete expects
                    response($.map(data.results, function(item) {
                        return {
                            label: item.text,
                            value: item.text
                        };
                    }));
                }
            });
        },
        minLength: 1,
        delay: 250,
        autoFocus: true,
        classes: {
            "ui-autocomplete": "dropdown-menu"
        }
    }).autocomplete("instance")._renderItem = function(ul, item) {
        // Custom rendering for Bootstrap styling
        return $("<li>")
            .append("<div class='dropdown-item'>" + item.label + "</div>")
            .appendTo(ul);
    };
    
    // Get initial value from the data attribute
    const manufacturerField = $('.manufacturer-autocomplete');
    const initialManufacturer = manufacturerField.data('initial-value');
    if (initialManufacturer) {
        // Create the option and append it
        const newOption = new Option(initialManufacturer, initialManufacturer, true, true);
        manufacturerField.append(newOption).trigger('change');
    }
    
    // Handle dynamic updates to room/rack/shelf filters
    const roomSelect = document.querySelector('select[name="room"]');
    const rackSelect = document.querySelector('select[name="rack"]');
    
    if (roomSelect && rackSelect) {
        roomSelect.addEventListener('change', function() {
            updateRacks(this.value);
        });
    }
    
    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert:not(.alert-danger)');
        alerts.forEach(function(alert) {
            if (alert.querySelector('.btn-close')) {
                alert.querySelector('.btn-close').click();
            }
        });
    }, 5000);

    // Handle dropdown hover states
    const dropdowns = document.querySelectorAll('.dropdown');
    
    dropdowns.forEach(dropdown => {
        // Ensure dropdown toggle arrow remains visible on hover
        const dropdownToggle = dropdown.querySelector('.dropdown-toggle');
        if (dropdownToggle) {
            dropdownToggle.addEventListener('mouseenter', function() {
                this.style.setProperty('content', '""', 'important');
            });
        }
    });
});

// Function to update racks dropdown based on selected room
function updateRacks(roomId) {
    const rackSelect = document.querySelector('select[name="rack"]');
    const shelfSelect = document.querySelector('select[name="shelf"]');
    
    if (!rackSelect) return;
    
    // Clear rack and shelf selects
    rackSelect.innerHTML = '<option value="">Wszystkie regały</option>';
    if (shelfSelect) {
        shelfSelect.innerHTML = '<option value="">Wszystkie półki</option>';
    }
    
    if (!roomId) return;
    
    // Get racks for the selected room via AJAX
    fetch(`/warehouse/api/racks/?room=${roomId}`)
        .then(response => response.json())
        .then(data => {
            data.forEach(rack => {
                const option = document.createElement('option');
                option.value = rack.id;
                option.textContent = `${rack.room_name}.${rack.name}`;
                rackSelect.appendChild(option);
            });
        });
}

// Function to update shelves dropdown based on selected rack
function updateShelves(rackId) {
    const shelfSelect = document.querySelector('select[name="shelf"]');
    
    if (!shelfSelect) return;
    
    // Clear shelf select
    shelfSelect.innerHTML = '<option value="">Wszystkie półki</option>';
    
    if (!rackId) return;
    
    // Get shelves for the selected rack via AJAX
    fetch(`/warehouse/api/shelves/?rack=${rackId}`)
        .then(response => response.json())
        .then(data => {
            data.forEach(shelf => {
                const option = document.createElement('option');
                option.value = shelf.id;
                option.textContent = `${shelf.full_location}`;
                shelfSelect.appendChild(option);
            });
        });
}
