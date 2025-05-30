document.addEventListener('DOMContentLoaded', function() {
    // Get map container
    const mapElement = document.getElementById('map');
    if (!mapElement) return;

    // Get data from data attributes
    const centerLat = mapElement.dataset.centerLat || 52.5200;
    const centerLng = mapElement.dataset.centerLng || 13.4050;
    const tutorsData = JSON.parse(mapElement.dataset.tutors || '[]');

    // Initialize map
    var map = L.map('map').setView([centerLat, centerLng], 11);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // Add markers (using Leaflet) (Leaflet is an open source JavaScript library for interactive maps.)
    tutorsData.forEach(function(tutor) {
        L.marker([tutor.latitude, tutor.longitude])
            .addTo(map)
            .bindPopup(`<b>${tutor.name}</b><br>${tutor.subjects}<br>${tutor.address}`);  // Alterado de zipcode para address
    });
});