$(document).ready(function() {

    // function listPapers() {
      
    // }

    const formatNumber = n => ("0" + n).slice(-2);
    const base_url = "http://monash-econ.s3-ap-southeast-2.amazonaws.com/metadata.json";
    let wpn = ""
    const date = new Date();
    const maxAllowedSize = 5 * 1024 * 1024; // 5 MB
    let currentYear = date.getFullYear(); 
    let currentPapers = 0;
    let prefix = `RePEc/ajr/sodwps/${currentYear}-`;
    // AWS credentials
    const bucketName = "monash-econ-wps";
    const bucketRegion = "ap-southeast-2";
    const IdentityPoolId = "ap-southeast-2:39b53048-8af5-475b-9c7e-24057d7f4b71";
    
    // aws cognito
    AWS.config.update({
      region: bucketRegion,
      credentials: new AWS.CognitoIdentityCredentials({
        IdentityPoolId: IdentityPoolId
      })
    });
    let s3 = new AWS.S3({
      // apiVersion: "2012-10-17",
      params: { Bucket: bucketName }
    });
    var params = { 
      Bucket: bucketName,
      Delimiter: '/',
      Prefix: prefix
     }
     // get the no of papers
     // Test - max key limit (1000?)
     s3.listObjects(params, function (error, data) {
      if (error){
        console.log(`Error ${error}`)
        $("#errorModal .modal-body").html("");
        $('#errorModal .modal-body').prepend(`<p><strong>Oops!</strong></p><p>An error has occurred. Please try again later.</p>`)
        $("#spinner").remove();
        $('button').prop('disabled', false);
        $('#errorModal').modal('show');
      }
      else{
        currentPapers = data.Contents.length / 2 // ignoring RDF files
        if (currentPapers > 0){ // if there are papers
          wpn = currentYear + "-" + formatNumber(currentPapers+1) // note: only handles 01-99
        }
        else{
          wpn = currentYear + "-" + "01"
        }
        $("#wpn").attr("placeholder", wpn); // set the placeholder
        $("#wpn").val(wpn)
      }
     });

    // $.ajax({
    //   type: "GET",
    //   // XDomainRequest protocol must be the same scheme as the calling page
    //   url: base_url, // ('https:' == document.location.protocol ? 'https://' : 'http://') +
    //   dataType: "json",
    //   success: function(data) {
    //     // console.log(data)
    //     // check if JSON file is stringified
    //     if (typeof data == 'string'){
    //       data = JSON.parse(data)
    //     }
    //     // console.log(data)
    //     currentYear = date.getFullYear();
    //     if (data.papers.length > 0){
    //       let currentPapers = data.papers.filter(a=>a.year==currentYear);
    //       wpn = currentYear + "-" + formatNumber(currentPapers.length+1) // note: only handles 01-99
    //     } 
    //     else{
    //       wpn = currentYear + "-" + "01"
    //     }
    //     $("#wpn").attr("placeholder", wpn); // set the placeholder
    //     $("#wpn").val(wpn)
    //   },
    //   error: function(error) {
    //     console.log(`Error ${error}`)
    //     $("#errorModal .modal-body").html("");
    //     $('#errorModal .modal-body').prepend(`<p><strong>Oops!</strong></p><p>An error has occurred. Please try again later.</p>`)
    //     $("#spinner").remove();
    //     $('button').prop('disabled', false);
    //     $('#errorModal').modal('show');
    //   }
    //   });
      
      // Add the following code if you want the name of the file appear on select
      $(".custom-file-input").on("change", function() {
        let fileName = $(this).val().split("\\").pop();
        $(this).siblings(".custom-file-label").addClass("selected").html(fileName);
      });

      $(document).on('click', '.btn-add', function(e) {
        e.preventDefault();
    
        var dynaForm = $('.dynamic-wrap'),
          currentEntry = $(this).parents('.entry:first'),
          newEntry = $(currentEntry.clone()).appendTo(dynaForm);
    
        newEntry.find('input').val('');
        dynaForm.find('.entry:not(:last) .btn-add')
          .removeClass('btn-add').addClass('btn-remove')
          .removeClass('btn-primary').addClass('btn-secondary')
          .html('<i class="fa fa-times"></i>');
      }).on('click', '.btn-remove', function(e) {
        $(this).parents('.entry:first').remove();
    
        e.preventDefault();
        return false;
      });

      $("#confirmSubmission").click(function(e) {
         // Fetch all the forms we want to apply custom Bootstrap validation styles to
        var form = document.getElementById('wpForm');
        if (form.checkValidity() === false) {
          event.preventDefault();
          event.stopPropagation();
          form.classList.add('was-validated');
        }
        else{

          fileSize = $('#inputFile')[0].files[0].size
          if (fileSize > maxAllowedSize){
            $("#errorModal .modal-body").html("");
            $('#errorModal .modal-body').prepend(`<p><strong>File too large.</strong></p><p>Please upload a PDF file which is less than 5 MB in size.</p>`)
            $("#spinner").remove();
            $('button').prop('disabled', false);
            $('#errorModal').modal('show');
          }
          else{
            $('#confirmModal').modal('show');
          }
        }
    });

    $("#closeBtn").click(function(e) {
      $('form').get(0).reset();
      window.location.reload();
    }); 

      $("#submitPaper").click(function(e) {
                  $('#confirmModal').modal('hide');
                  $('button').prop('disabled', true);
                  $('#confirmSubmission').prepend(`<span id="spinner" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>`);
                  console.log('Processing ..')
                  let base64;
                  let author = [];
                  var reader = new FileReader(),
                  file = $('#inputFile')[0];
                  $('.dynamic-wrap input').each(function(index){ author.push($(this).val()) });
                  reader.onload = function () {
                      let result = reader.result;
                      base64 = result.replace(/^[^,]*,/, '')
                      // all values are string
                      let data = {
                        wpn : $('#wpn').val(),
                        title: $('#title').val(),
                        email: $('#email').val(),
                        author: author.join(', '),
                        keyword: $("#keyword").tagsinput('items').join(', '),
                        jel_code:  $('#jel').val(),
                        abstract: encodeURIComponent($('#abstract').val()),
                        pub_online:  date.getDate() + ' ' + date.toLocaleString('default', { month: 'long' }) + ' ' + date.getFullYear(),
                        file: base64
                    }

                $.ajax({
                    url: "https://5v0dil8zg2.execute-api.ap-southeast-2.amazonaws.com/v1/upload",
                    type: "POST",
                    contentType: 'application/json',
                    dataType: 'json',
                    accept: 'application/json',
                    processData: true,
                    data: data,
                    success: function (response) {
                      console.log(response)      
                      $("#messageModal .modal-body").html("");
                      $('#messageModal .modal-body').prepend(`<p><strong>Done!</strong></p><p>Your paper has been successfully submitted. Here's the link below:</p><p><a href="${response.body.url}">${response.body.url}</a></p>`)
                        $("#spinner").remove();
                        $('button').prop('disabled', false);
                        $('#messageModal').modal('show');
                        console.log('Done!')
                    },
                    error: function(){
                        console.log("error!") 
                        $("#errorModal .modal-body").html("");
                        $('#errorModal .modal-body').prepend(`<p><strong>Oops!</strong></p><p>There's been an error.</p>`)
                        $("#spinner").remove();
                        $('button').prop('disabled', false);
                        $('#errorModal').modal('show');
                    }
                });
                  };
                  reader.readAsDataURL(file.files[0]);
            // }
          });
  });