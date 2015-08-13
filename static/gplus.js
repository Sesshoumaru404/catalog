function signInCallback(authResult) {
  var csrftoken = $('meta[name=csrf-token]').attr('content')
 if (authResult) {
   //Hide the sign-in button now that the use is authorized,
   $('#signinButton').attr('style','display:none')

   $.ajaxSetup({
       beforeSend: function(xhr, settings) {
           if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
               xhr.setRequestHeader("X-CSRFToken", csrftoken)
           }
       }
   })

    var csrftoken = "{{ csrf_token() }}"
    console.log(csrftoken)
   $.ajax({
      type: 'POST',
      url: '/gconnect?state={{STATE}}',
      processData: false,
      contentType: 'application/octet-stream; charset=utf-8',
      data: authResult['code'],
      success: function(result) {
        console.log('hey')
        // Handle or verify the server response if necessary.
        if (result) {
          $('#result').html('Login Successful!</br>'+ result + '</br>Redirecting...')
            setTimeout(function() {
              window.location.href = "/restaurant";
            }, 4000);
        } else if (authResult['error']) {
          console.log('There was an error: ' + authResult['error']);
        } else {
          $('#result').html('Failed to make a server-side call. Check your configuration and console.');
        }
      }
    })
  }
}
