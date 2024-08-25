<?php
if ($_SERVER["REQUEST_METHOD"] == "POST") {
    // Retrieve form data
    $name = $_POST["name"];
    $email = $_POST["email"];
    $phone = $_POST["phone"];
    $message = $_POST["message"];
    
    // Your email settings (you need to configure this)
    $to = "mo@relengine.com"; // Replace with your email address
    $subject = "Contact Form Submission from $name";
    $headers = "From: $email";
    
    // Compose the email message
    $email_message = "Name: $name\n";
    $email_message .= "Email: $email\n";
    $email_message .= "Phone: $phone\n\n";
    $email_message .= "Message:\n$message";
    
    // Send the email
    if (mail($to, $subject, $email_message, $headers)) {
        // Email sent successfully
        $message = "Thank you, $name! Your message has been sent successfully.";
        $status = "success";
    } else {
        // Error sending email
        $message = "Sorry, there was an error sending your message. Please try again later.";
        $status = "error";
    }
    
    // Redirect back to the HTML page with the flashed message
    header("Location: contact.html?status=$status&message=$message");
} else {
    // Handle the case where the form was not submitted properly
    echo "Invalid request!";
}
?>
