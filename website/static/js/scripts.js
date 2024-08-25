// // function searchKeyword_custo(formData) {
// //   // Select the form element by its ID
// //   var formElement = document.getElementById('search-form');

// //   // Send a POST request to the server
// //   fetch("{{ url_for('jour.search_page') }}", {
// //     method: "POST",
// //     body: JSON.stringify(formData),
// //   }).then((data) => {
// //       if (data.success) {
// //         alert('Search successful!');
// //         window.location.href = data.redirectURL; // Redirect to the specified URL
// //       } 
// //     });

// // }

// function submitForm() {
//     var searchInput = $('#search_input').val();
//     var form = document.getElementById('search-form');
//     form.action = "{{ url_for('jour.search_result', keyword='') }}" + encodeURIComponent(searchInput);
//     form.submit();
// }
