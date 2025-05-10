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
    $('.item-autocomplete').select2({
        theme: 'bootstrap-5',
        placeholder: 'Wpisz nazwę przedmiotu',
        minimumInputLength: 2,
        tags: true,
        createTag: function(params) {
            return {
                id: params.term,
                text: params.term,
                newOption: true
            };
        },
        ajax: {
            url: '/warehouse/api/autocomplete/items/',
            dataType: 'json',
            delay: 250,
            data: function (params) {
                return {
                    term: params.term
                };
            },
            processResults: function (data) {
                return {
                    results: data.results
                };
            },
            cache: true
        }
    });
    
    // Initialize manufacturer autocomplete
    $('.manufacturer-autocomplete').select2({
        theme: 'bootstrap-5',
        placeholder: 'Wpisz producenta',
        minimumInputLength: 2,
        tags: true,
        createTag: function(params) {
            return {
                id: params.term,
                text: params.term,
                newOption: true
            };
        },
        ajax: {
            url: '/warehouse/api/autocomplete/manufacturers/',
            dataType: 'json',
            delay: 250,
            data: function (params) {
                return {
                    term: params.term
                };
            },
            processResults: function (data) {
                return {
                    results: data.results
                };
            },
            cache: true
        }
    });
    
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
