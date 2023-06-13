document.getElementById("uploadinput").addEventListener("change", function (event) {
    uploadFile(document.getElementById("uploadinput").files[0]);
});

const dropArea = document.querySelector(".drag-area"),
dragText = dropArea.querySelector("header"),
input = dropArea.querySelector("input");

dropArea.addEventListener("drop", function (event) {
    event.preventDefault();
    var files = event.dataTransfer.files;
    uploadFile(files[0]);
});


//Drag File Over DropArea
dropArea.addEventListener("dragover", (event)=>{
  event.preventDefault();
  dropArea.classList.add("active");
  dragText.textContent = "Release to Upload File";
});

//Leave DropArea with dragged File
dropArea.addEventListener("dragleave", ()=>{
  dropArea.classList.remove("active");
  dragText.textContent = "Drag & Drop to Upload File";
});

const data = document.currentScript.dataset;
const csrfToken = data.token;
function uploadFile(file) {
    var formData = new FormData();
    formData.append('csrfmiddlewaretoken', csrfToken);
    formData.append('uploadfile', file);
    $.ajax({
            type: "POST",
            url: "upload/",   
            contentType: false,
            processData: false,
            data: formData,
            success:  function(response){
                console.log(response);
                alert(response);
                window.location.reload();
            },
            error:  function(response){
                console.log(response.responseText);
                alert(response.responseText);
                window.location.reload();
            }
    //TODO get multiple files running
    //var alerttxt = "";
    //for( var i=0; i<files.length; i++) {
    //    var formData = new FormData();
    //    formData.append('csrfmiddlewaretoken', '{{ csrf_token }}');
    //    formData.append("uploadfile", files[i]);
    //    //formData.append('uploadfile', event.dataTransfer.files[0]);
    //    $.ajax({
    //            type: "POST",
    //            url: "upload/",   
    //            contentType: false,
    //            processData: false,
    //            data: formData,
    //            success:  function(response){
    //                alerttxt = alerttxt + response + "\n";
    //                //alert(response);
    //            }
    //    });
    //}
    //alert(alerttxt);
    });

}
