function deleteNote(noteId) {
  fetch("/delete-note", {
    method: "POST",
    body: JSON.stringify({ noteId: noteId }),
  }).then((_res) => {
    window.location.href = "/";
  });
}

function deleterev(noteId) {
    fetch("{{ url_for('jour.delete_review') }}", {
        method: "POST",
        body: JSON.stringify({ noteId: noteId }),
    }).then((_res) => {
        window.location.reload(); // Refresh the page
    });
}

function upvote(noteId) {
    fetch("{{ url_for('jour.upvote_rev') }}", {
        method: "POST",
        body: JSON.stringify({ noteId: noteId }),
    }).then((_res) => {
        window.location.reload(); // Refresh the page
    });}

function loginAndHidePopup(formData) {
    fetch("{{ url_for('auth.login_popup') }}", {
      method: "POST",
      body: JSON.stringify(formData)
    })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        // Handle successful login
        alert('Logged in successfully!');
        $('#loginModal').modal('hide'); // Close the popup
        // You can add further logic to update the UI here
      } else {
        // Handle login failure
        alert('Login failed: ' + data.message);
      }
    })
    .catch((error) => {
      console.error('An error occurred:', error);
      alert('An error occurred while processing your request. Please try again.');
    });
  }
  


