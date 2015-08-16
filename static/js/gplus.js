function signInCallback(authResult) {
  var csrftoken = $('meta[name=csrf-token]').attr('content')
  var state = $('meta[name=STATE]').attr('content')
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
   function flash(result) {
     $('.flash').html('<div id="flashBox" class="alert alert-warning alert-dismissible fade in flash" role="alert"><button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">×</span></button><ul><li><strong> Alert </strong>'+result+' Redirecting...</li></ul></div>')
   }
  //  flash('test')
   $.ajax({
      type: 'POST',
      url: '/connect?state=' + state,
      processData: false,
      contentType: 'application/octet-stream; charset=utf-8',
      data: authResult['code'],
      success: function(result) {
        console.log(result)
        // Handle or verify the server response if necessary.
        if (result) {
          $('#result').html('Login Successful!</br>'+ result + '</br>Redirecting...')
            setTimeout(function() {
              window.location.href = "#";
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
