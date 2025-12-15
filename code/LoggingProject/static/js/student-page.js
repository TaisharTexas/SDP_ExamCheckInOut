
function openEditStudentModal(fname, lname, url) {
  
  //alert("hellow world");
  
  document.getElementById('edit_student').style.display = 'block';

    document.querySelector('input[name="student_first_name"]').value = fname;
    document.querySelector('input[name="student_last_name"]').value = lname;

    var form = document.getElementById('edit_student_form');
    form.action = url



}
