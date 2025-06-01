$(function() { 
    //This is a jQuery function that is equivalent to document.addEventListener('DOMContentLoaded', function() { ... })
    $("#address").autocomplete({
      source: function(request, response) {
        // Automatically add "Berlin" to the query if it is not present
        let searchTerm = request.term;
        if (!searchTerm.toLowerCase().includes('berlin')) {
          searchTerm += ', Berlin, Germany';
        }
  
        $.ajax({
          url: "https://nominatim.openstreetmap.org/search",
          dataType: "json",
          data: {
            q: searchTerm,
            format: "json",
            addressdetails: 1,
            limit: 10,  // number of results to return
            countrycodes: "de",
            viewbox: "13.1,52.3,13.6,52.7",  // Berlin's bounding box
            bounded: 1
          },
          success: function(data) {
            response($.map(data, function(item) {
              return {
                label: item.display_name,
                value: item.display_name,
                lat: item.lat,
                lon: item.lon,
                district: item.address.suburb || item.address.city_district || item.address.district || "",
                postcode: item.address.postcode || ""
              };
            }));
          }
        });
      },
      minLength: 3, //It only starts searching after the user has entered at least 3 characters
      delay: 200,  // Wait half a second before making an appointment
      select: function(event, ui) {
        // Fill in hidden fields automatically
        $("#latitude").val(ui.item.lat);
        $("#longitude").val(ui.item.lon);
        $("#location").val(ui.item.district);
        $("#zipcode").val(ui.item.postcode);
      }
    });
  });